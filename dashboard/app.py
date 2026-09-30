"""
app.py - Advanced Interactive Cyber-NOC Dashboard for Intelligent Self-Healing SDN.

Features:
- Dynamic topology generation (Canonical, Spine-Leaf, Redundant Mesh, Chordal Ring)
- Configurable switch counts (4 to 20 nodes) and arbitrary link failure targeting
- Dynamic time-scrubber & playback animation showing packet transit, link cuts, and live rerouting
- Real-time telemetry, baseline comparison, and interactive terminal event streaming
"""

import sys
import time
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from src.config import SimulationConfig
from src.topology.topology_manager import TopologyManager
from src.simulation.traffic_simulator import TrafficSimulator
from src.analytics.analytics_engine import (
    create_topology_plotly_fig,
    create_time_series_plotly_fig,
)
from experiments.baseline import run_baseline_comparison

# Streamlit Page Setup
st.set_page_config(
    page_title="SDN Self-Healing NOC",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Cyber-NOC Dark CSS Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 15% 15%, #0f172a 0%, #060813 100%);
        color: #f1f5f9;
    }

    /* Glassmorphism Cards */
    .noc-card {
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        margin-bottom: 12px;
    }

    .noc-header {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.02em;
        margin-bottom: 2px;
    }

    .noc-sub {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 18px;
    }

    /* Metric Badges */
    .status-badge-healthy {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
    }

    .status-badge-fault {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
    }

    .status-badge-rerouted {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.82rem;
        display: inline-block;
    }

    .route-box {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
        background: #090d16;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 10px 14px;
        color: #38bdf8;
        margin-top: 6px;
    }

    /* Streamlit widget tweaks */
    div[data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        color: #f8fafc;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_available_links_from_topo(tm: TopologyManager):
    """Returns sorted list of link tuples for selectbox."""
    return [tuple(sorted((u, v))) for u, v, _ in tm.get_all_links()]


def main():
    # Header Banner
    st.markdown("<div class='noc-header'>⚡ SDN Autonomous Self-Healing Operations Center</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='noc-sub'>Dynamic Topology Architect • Discrete-Event Traffic Forwarding • Closed-Loop Fault Recovery</div>",
        unsafe_allow_html=True,
    )

    # Sidebar: Dynamic Topology & Simulation Configuration
    st.sidebar.markdown("### 🛠️ Topology Architect")

    topo_family = st.sidebar.selectbox(
        "Network Topology Architecture",
        options=["canonical", "spine_leaf", "mesh", "ring"],
        format_func=lambda x: {
            "canonical": "⚡ Canonical Benchmark (2 Hosts, 5 Switches)",
            "spine_leaf": "☁️ Cloud Spine-Leaf Data Center Fabric",
            "mesh": "🕸️ Scalable Redundant Mesh Network",
            "ring": "🔄 Resilient Chordal Ring Fabric",
        }[x],
        help="Select standard benchmark or dynamically generate multi-switch cloud topologies.",
    )

    if topo_family == "canonical":
        num_switches = 5
        st.sidebar.caption("Canonical topology: 2 Hosts, 5 Switches, Dual-path diamond.")
    else:
        num_switches = st.sidebar.slider(
            "Number of SDN Switches",
            min_value=4,
            max_value=16,
            value=8 if topo_family != "spine_leaf" else 6,
            step=1,
            help="Dynamically scale the number of intermediate forwarding switches in the fabric.",
        )

    # Initialize dynamic topology manager
    tm = TopologyManager(topology_type=topo_family, num_switches=num_switches)
    all_links = get_available_links_from_topo(tm)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎯 Fault & Traffic Target")

    # Select Link to Disrupt dynamically
    target_link = st.sidebar.selectbox(
        "Target Physical Link to Sever",
        options=all_links,
        format_func=lambda pair: f"Link ({pair[0]} ── {pair[1]})",
        index=min(2, len(all_links) - 1),
        help="Choose any link in the dynamic network to sever during the simulation.",
    )

    routing_mode = st.sidebar.selectbox(
        "Control-Plane Operating Mode",
        options=["self_healing", "static"],
        format_func=lambda x: "🟢 Self-Healing (Autonomous Dijkstra Reroute)" if x == "self_healing" else "🔴 Static Routing (No Recovery Baseline)",
        help="Self-healing dynamically updates flow rules. Static leaves stale paths causing drops.",
    )

    sim_duration = st.sidebar.slider("Simulation Window (Units)", 15.0, 60.0, 30.0, 5.0)
    packet_rate = st.sidebar.slider("Traffic Generation Rate (pkts/unit)", 1.0, 15.0, 5.0, 1.0)
    failure_time = st.sidebar.slider("Fault Inception Time (t)", 5.0, sim_duration - 5.0, 10.0, 1.0)
    heartbeat_interval = st.sidebar.slider("Heartbeat Probe Interval", 0.5, 3.0, 1.0, 0.5)

    st.sidebar.markdown("---")
    run_sim_btn = st.sidebar.button("🚀 Run Dynamic Simulation", type="primary", use_container_width=True)

    # Simulation Execution in Session State
    sim_cache_key = f"{topo_family}_{num_switches}_{target_link}_{routing_mode}_{sim_duration}_{packet_rate}_{failure_time}_{heartbeat_interval}"

    if "last_sim_key" not in st.session_state or st.session_state["last_sim_key"] != sim_cache_key or run_sim_btn:
        cfg = SimulationConfig(
            simulation_duration=sim_duration,
            packet_rate=packet_rate,
            failure_time=failure_time,
            heartbeat_interval=heartbeat_interval,
            failed_link=target_link,
            routing_mode=routing_mode,
        )
        sim = TrafficSimulator(cfg, topology_manager=tm)
        sim_res = sim.run()
        st.session_state["sim_res"] = sim_res
        st.session_state["tm"] = tm
        st.session_state["last_sim_key"] = sim_cache_key

    sim_res = st.session_state["sim_res"]
    tm = st.session_state["tm"]
    metrics = sim_res.summary_metrics

    # Top KPI Ribbon
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    with kpi1:
        st.metric("Total Generated", f"{metrics['packets_sent']} pkts")
    with kpi2:
        st.metric("Delivered Traffic", f"{metrics['packets_received']} pkts")
    with kpi3:
        pdr_val = metrics['pdr_pct']
        st.metric("Packet Delivery Ratio", f"{pdr_val}%", delta=f"{pdr_val - 50:.1f}% vs baseline")
    with kpi4:
        st.metric("Packet Loss", f"{metrics['packet_loss_pct']}%", delta=f"-{70 - metrics['packet_loss_pct']:.1f}% drop" if routing_mode == "self_healing" else "+High Loss", delta_color="inverse")
    with kpi5:
        rec_time_str = f"{metrics['recovery_time']} units" if routing_mode == "self_healing" else "No Recovery"
        st.metric("Restoration Latency", rec_time_str)

    # Main Tabs
    tab_playback, tab_analytics, tab_baseline, tab_logs, tab_packets = st.tabs(
        [
            "🎬 Dynamic Topology & Playback",
            "📈 Traffic Trajectory",
            "⚖️ Static vs Self-Healing Benchmark",
            "💻 Controller Event Console",
            "📦 Packet Telemetry Inspector",
        ]
    )

    with tab_playback:
        st.markdown("#### ⏱️ Dynamic Simulation Playback & Time-Scrubber")
        st.caption("Drag the slider to observe how the SDN controller dynamically updates paths, detects failures, and heals the network at any point in simulation time.")

        # Interactive Time Scrubber Slider
        max_time = sim_duration
        current_time_scrub = st.slider(
            "Simulation Clock (Time Units):",
            min_value=0.0,
            max_value=max_time,
            value=max_time,
            step=1.0,
            format="t = %.1f units",
        )

        # Find snapshot for current_time_scrub
        snapshots = sim_res.snapshots
        curr_snap = None
        if snapshots:
            for s in snapshots:
                if s["time"] <= current_time_scrub:
                    curr_snap = s
                else:
                    break
        if not curr_snap and snapshots:
            curr_snap = snapshots[0]

        # Determine route and link states at scrubbed time
        if curr_snap:
            display_route = curr_snap["route"]
            display_phase = curr_snap["phase"]
            display_label = curr_snap["phase_label"]
            snap_delivered = curr_snap["delivered"]
            snap_dropped = curr_snap["dropped"]
            snap_pdr = curr_snap["pdr"]
        else:
            display_route = sim_res.final_route
            display_phase = "NORMAL"
            display_label = "🟢 Normal Operational State"
            snap_delivered = metrics["packets_received"]
            snap_dropped = metrics["packets_lost"]
            snap_pdr = metrics["pdr_pct"]

        # Link status at this time
        is_link_cut_now = current_time_scrub >= failure_time
        active_failed_link = target_link if is_link_cut_now else None

        # Two-column layout for Graph + Live Diagnostics
        g_col, d_col = st.columns([3, 2])

        with g_col:
            title_text = f"Fabric State at t = {current_time_scrub:.1f} ({display_label})"
            topo_fig = create_topology_plotly_fig(
                topology_manager=tm,
                active_route=display_route,
                failed_link=active_failed_link,
                title=title_text,
                dark_mode=True,
            )
            st.plotly_chart(topo_fig, use_container_width=True)

        with d_col:
            st.markdown("##### 📡 Instantaneous Network Diagnostics")

            if display_phase == "NORMAL":
                st.markdown(f"<span class='status-badge-healthy'>{display_label}</span>", unsafe_allow_html=True)
            elif display_phase == "FAULT_ACTIVE":
                st.markdown(f"<span class='status-badge-fault'>{display_label}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"<span class='status-badge-rerouted'>{display_label}</span>", unsafe_allow_html=True)

            st.markdown("**Installed Forwarding Path:**")
            path_str = " → ".join(display_route) if display_route else "No Route Installed"
            st.markdown(f"<div class='route-box'>{path_str}</div>", unsafe_allow_html=True)

            st.markdown(f"**Target Link State ({target_link[0]} ── {target_link[1]}):**")
            if is_link_cut_now:
                st.error(f"❌ LINK SEVERED at t = {failure_time:.1f} units")
            else:
                st.success(f"✔️ LINK OPERATIONAL (Scheduled cut at t = {failure_time:.1f})")

            st.markdown("**Instantaneous Telemetry at t:**")
            sub_col1, sub_col2, sub_col3 = st.columns(3)
            with sub_col1:
                st.metric("Delivered", f"{snap_delivered} pkts")
            with sub_col2:
                st.metric("Dropped", f"{snap_dropped} pkts")
            with sub_col3:
                st.metric("Live PDR", f"{snap_pdr}%")

            if routing_mode == "self_healing" and current_time_scrub >= (sim_res.recovery_record.get('reroute_time') or 999):
                rec = sim_res.recovery_record
                st.info(f"⚡ Self-Healing Completed in **{rec.get('total_recovery_time', 'N/A')} units** (Detection: {rec.get('detection_delay', 'N/A')} | Reroute: {rec.get('reroute_delay', 'N/A')})")

    with tab_analytics:
        st.markdown("#### 📈 Continuous Telemetry & Traffic Trajectory")
        det_timestamp = (
            sim_res.recovery_record.get("detection_time")
            if sim_res.recovery_record and routing_mode == "self_healing"
            else None
        )
        ts_fig = create_time_series_plotly_fig(
            time_series_df=sim_res.time_series_df,
            failure_time=failure_time,
            detection_time=det_timestamp,
            title=f"Traffic Throughput & Drop Spikes (Fault Injected at t={failure_time:.1f})",
            dark_mode=True,
        )
        st.plotly_chart(ts_fig, use_container_width=True)

        # Delay & Throughput Statistics
        c_an1, c_an2 = st.columns(2)
        with c_an1:
            st.markdown("##### End-to-End Latency Profile")
            st.write(f"- **Mean Latency:** `{metrics['avg_delay']} units`")
            st.write(f"- **Min Latency (Primary Path):** `{metrics['min_delay']} units`")
            st.write(f"- **Max Latency (Alternate Path):** `{metrics['max_delay']} units`")
        with c_an2:
            st.markdown("##### Effective Bandwidth")
            st.write(f"- **Delivered Throughput:** `{metrics['throughput_kbps']} kbps`")
            st.write(f"- **Packet Transfer Rate:** `{metrics['throughput_pps']} pkts/unit`")

    with tab_baseline:
        st.markdown("#### ⚖️ Empirical Baseline Comparison: Static Routing vs Self-Healing SDN")
        st.caption("Validates the core experimental hypothesis by running an identical simulation under Static Routing (no controller recovery) vs. Self-Healing SDN.")

        with st.spinner("Generating real-time comparative benchmark..."):
            res_stat, res_sh, comp_df = run_baseline_comparison(
                simulation_duration=sim_duration,
                packet_rate=packet_rate,
                failure_time=failure_time,
                heartbeat_interval=heartbeat_interval,
                save_outputs=False,
            )

        b_c1, b_c2 = st.columns([1, 1])
        with b_c1:
            st.markdown("##### Benchmark Metrics Table")
            st.dataframe(comp_df, use_container_width=True)

        with b_c2:
            st.markdown("##### Key Performance Delta")
            m_s = res_stat.summary_metrics
            m_h = res_sh.summary_metrics

            fig_bar = go.Figure(
                data=[
                    go.Bar(
                        name="Static (No Recovery)",
                        x=["PDR (%)", "Packet Loss (%)", "Throughput (kbps)"],
                        y=[m_s["pdr_pct"], m_s["packet_loss_pct"], m_s["throughput_kbps"]],
                        marker_color="#ef4444",
                    ),
                    go.Bar(
                        name="Self-Healing SDN",
                        x=["PDR (%)", "Packet Loss (%)", "Throughput (kbps)"],
                        y=[m_h["pdr_pct"], m_h["packet_loss_pct"], m_h["throughput_kbps"]],
                        marker_color="#10b981",
                    ),
                ]
            )
            fig_bar.update_layout(
                barmode="group",
                paper_bgcolor="#0b1120",
                plot_bgcolor="#0b1120",
                font=dict(color="#f8fafc"),
                margin=dict(l=20, r=20, t=30, b=20),
                height=320,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab_logs:
        st.markdown("#### 💻 SDN Controller Real-Time Event Stream")
        log_df = pd.DataFrame(sim_res.event_log)
        if not log_df.empty:
            st.dataframe(log_df, use_container_width=True, height=360)
        else:
            st.info("No controller events recorded.")

    with tab_packets:
        st.markdown("#### 📦 Packet-Level Telemetry Inspector")
        df_packets = sim_res.packets_df

        if not df_packets.empty:
            status_filter = st.multiselect(
                "Filter Packet Status:",
                options=df_packets["status"].unique(),
                default=df_packets["status"].unique(),
            )
            filtered_df = df_packets[df_packets["status"].isin(status_filter)]
            st.dataframe(filtered_df, use_container_width=True, height=360)
            st.download_button(
                "📥 Export Telemetry CSV",
                data=filtered_df.to_csv(index=False),
                file_name="telemetry_packets.csv",
                mime="text/csv",
            )
        else:
            st.info("No packet records available.")


if __name__ == "__main__":
    main()
