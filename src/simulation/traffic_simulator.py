"""
traffic_simulator.py - SimPy discrete-event SDN traffic and control-plane simulation.

Simulates packet generation at end-hosts, hop-by-hop forwarding through switches,
scheduled physical link failures, explicit heartbeat-based failure detection,
dynamic controller rerouting (in self-healing mode) or unrecovered drops (in static mode),
and telemetry collection.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import simpy
import random

from src.config import SimulationConfig
from src.topology.topology_manager import TopologyManager
from src.routing.dijkstra_router import DijkstraRouter
from src.controller.sdn_controller import SDNController
from src.failure.failure_injector import FailureInjector
from src.failure.failure_detector import FailureDetector
from src.recovery.recovery_engine import RecoveryEngine
from src.metrics.metrics_collector import MetricsCollector
from src.simulation.packet import Packet, PacketStatus


@dataclass
class SimulationResult:
    """Encapsulates all results, logs, and datasets from a simulation run."""
    config: SimulationConfig
    summary_metrics: Dict[str, Any]
    packets_df: Any  # pd.DataFrame
    time_series_df: Any  # pd.DataFrame
    event_log: List[Dict[str, Any]]
    recovery_record: Optional[Dict[str, Any]]
    initial_route: List[str]
    final_route: List[str]


class TrafficSimulator:
    """Discrete-event SDN traffic simulator using SimPy."""

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        random.seed(self.config.random_seed)

        # Core components
        self.topology_manager = TopologyManager(
            default_bandwidth=self.config.default_bandwidth,
            default_delay=self.config.default_delay,
        )
        self.router = DijkstraRouter(weight_attribute="cost")
        self.controller = SDNController(
            topology_manager=self.topology_manager,
            router=self.router,
            routing_mode=self.config.routing_mode,
        )
        self.failure_injector = FailureInjector(self.topology_manager)
        self.failure_detector = FailureDetector(
            controller=self.controller,
            topology_manager=self.topology_manager,
            heartbeat_interval=self.config.heartbeat_interval,
        )
        self.recovery_engine = RecoveryEngine(
            controller=self.controller,
            topology_manager=self.topology_manager,
        )
        self.metrics_collector = MetricsCollector(
            simulation_duration=self.config.simulation_duration,
            packet_size_bytes=self.config.packet_size_bytes,
        )

        self.initial_route: List[str] = []
        self.latest_recovery: Optional[Dict[str, Any]] = None

    def run(self) -> SimulationResult:
        """
        Executes the discrete-event simulation from t=0.0 to t=simulation_duration.

        Returns:
            SimulationResult containing metrics, dataframes, and logs.
        """
        env = simpy.Environment()

        # Compute initial route before traffic begins
        self.initial_route = self.controller.get_route(
            self.config.source_host, self.config.destination_host
        ) or []

        # Start SimPy background processes
        env.process(self._traffic_generator_process(env))
        env.process(self._heartbeat_process(env))

        # Schedule link failure if within simulation window
        if self.config.failure_time < self.config.simulation_duration:
            env.process(self._failure_injector_process(env))

        # Execute simulation
        env.run(until=self.config.simulation_duration)

        # Obtain final route
        final_route = self.controller.get_route(
            self.config.source_host, self.config.destination_host
        ) or []

        return SimulationResult(
            config=self.config,
            summary_metrics=self.metrics_collector.get_summary_metrics(),
            packets_df=self.metrics_collector.get_packets_dataframe(),
            time_series_df=self.metrics_collector.get_time_series_metrics(),
            event_log=self.controller.get_event_log(),
            recovery_record=self.recovery_engine.get_latest_recovery(),
            initial_route=self.initial_route,
            final_route=final_route,
        )

    def _traffic_generator_process(self, env: simpy.Environment):
        """Generates packets at source host with configured inter-arrival time."""
        packet_id = 1
        inter_arrival = 1.0 / max(0.1, self.config.packet_rate)

        while env.now < self.config.simulation_duration:
            packet = Packet(
                packet_id=packet_id,
                source=self.config.source_host,
                destination=self.config.destination_host,
                creation_time=env.now,
                size_bytes=self.config.packet_size_bytes,
            )
            env.process(self._packet_transit_process(env, packet))
            packet_id += 1
            yield env.timeout(inter_arrival)

    def _packet_transit_process(self, env: simpy.Environment, packet: Packet):
        """Simulates hop-by-hop forwarding of a packet across network links."""
        # Query controller for current installed forwarding path
        route = self.controller.get_route(packet.source, packet.destination)

        if not route or len(route) < 2:
            packet.mark_dropped(packet.source, "NO_VALID_ROUTE")
            self.metrics_collector.record_packet(packet)
            return

        # Mark if packet is using alternate route
        if route != self.initial_route:
            packet.is_rerouted = True

        packet.mark_in_transit(initial_node=route[0], route=route)

        # Traverse each hop
        for i in range(len(route) - 1):
            curr_node = route[i]
            next_node = route[i + 1]

            # Check if link is currently active
            try:
                link_status = self.topology_manager.get_link_status(curr_node, next_node)
            except ValueError:
                link_status = "DOWN"

            if link_status != "UP":
                # Link is broken: packet is dropped at curr_node
                packet.mark_dropped(
                    curr_node, f"LINK_DOWN ({curr_node}-{next_node})"
                )
                self.metrics_collector.record_packet(packet)
                return

            # Simulate link propagation and transmission delay
            link_delay = self.config.default_delay
            yield env.timeout(link_delay)

            # Check if link broke while packet was in transit
            try:
                post_delay_status = self.topology_manager.get_link_status(curr_node, next_node)
            except ValueError:
                post_delay_status = "DOWN"

            if post_delay_status != "UP":
                packet.mark_dropped(
                    curr_node, f"IN_TRANSIT_LINK_FAILURE ({curr_node}-{next_node})"
                )
                self.metrics_collector.record_packet(packet)
                return

            packet.current_node = next_node

        # Reached destination successfully
        packet.mark_delivered(delivery_time=env.now)
        self.metrics_collector.record_packet(packet)

    def _failure_injector_process(self, env: simpy.Environment):
        """Simulates scheduled physical link disruption at configured failure_time."""
        yield env.timeout(self.config.failure_time)
        u, v = self.config.failed_link
        self.failure_injector.inject_link_failure(u, v, failure_time=env.now)
        self.controller.log_event(
            env.now,
            "FAILURE_INJECTED",
            f"Physical failure injected on link ({u}, {v}) at t={env.now:.2f}",
        )

    def _heartbeat_process(self, env: simpy.Environment):
        """Periodically runs health check probes to simulate explicit failure detection."""
        interval = self.config.heartbeat_interval
        while True:
            yield env.timeout(interval)
            new_failures = self.failure_detector.check_for_failures(
                current_time=env.now,
                known_failures=self.failure_injector.active_failures,
            )

            # If new failures discovered and self-healing is active, trigger recovery engine
            for f in new_failures:
                u, v = f["link"]
                f_time = f["failure_time"]
                d_time = f["detection_time"]

                rec_result = self.recovery_engine.trigger_recovery(
                    failed_u=u,
                    failed_v=v,
                    failure_time=f_time,
                    detection_time=d_time,
                )
                self.metrics_collector.record_recovery(rec_result)
