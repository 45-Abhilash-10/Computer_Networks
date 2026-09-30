"""
analytics_engine.py - Visualizations and comparative analytics for SDN simulation.

Builds interactive Plotly diagrams for the Streamlit dashboard and saves
publication-quality Matplotlib figures for reporting and project evaluation.
"""

from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt

from src.topology.topology_manager import TopologyManager


def create_topology_plotly_fig(
    topology_manager: TopologyManager,
    active_route: Optional[List[str]] = None,
    failed_link: Optional[Tuple[str, str]] = None,
    title: str = "SDN Topology State",
) -> go.Figure:
    """
    Renders an interactive 2D network graph in Plotly.
    Distinguishes between Hosts and Switches, highlights active routing paths,
    and visually flags failed links in red.
    """
    pos = topology_manager.get_node_positions()
    graph = topology_manager.get_graph()

    # Route edge set for quick lookup
    route_edges = set()
    if active_route and len(active_route) > 1:
        for i in range(len(active_route) - 1):
            route_edges.add(tuple(sorted((active_route[i], active_route[i + 1]))))

    failed_pair = tuple(sorted(failed_link)) if failed_link else None

    fig = go.Figure()

    # 1. Draw Links (Edges)
    for u, v, data in graph.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_pair = tuple(sorted((u, v)))
        status = data.get("status", "UP")

        if edge_pair == failed_pair or status == "DOWN":
            # Failed Link: Red dashed line
            line_color = "#e74c3c"
            line_width = 4
            line_dash = "dash"
            hover_text = f"FAILED LINK: {u} <-> {v}<br>Status: DOWN"
        elif edge_pair in route_edges:
            # Active Forwarding Route: Bright Green thick line
            line_color = "#2ecc71"
            line_width = 5
            line_dash = "solid"
            hover_text = f"ACTIVE ROUTE: {u} <-> {v}<br>Cost: {data.get('cost')}, Delay: {data.get('delay')} units"
        else:
            # Normal Inactive Link: Slate gray
            line_color = "#7f8c8d"
            line_width = 2
            line_dash = "solid"
            hover_text = f"Link: {u} <-> {v}<br>Cost: {data.get('cost')}, Delay: {data.get('delay')} units"

        fig.add_trace(
            go.Scatter(
                x=[x0, x1],
                y=[y0, y1],
                mode="lines",
                line=dict(color=line_color, width=line_width, dash=line_dash),
                hoverinfo="text",
                text=hover_text,
                showlegend=False,
            )
        )

    # 2. Draw Nodes (Hosts vs Switches)
    host_x, host_y, host_names, host_hover = [], [], [], []
    switch_x, switch_y, switch_names, switch_hover = [], [], [], []

    for node, data in graph.nodes(data=True):
        x, y = pos[node]
        node_type = data.get("type", "switch")
        label = data.get("label", node)

        if node_type == "host":
            host_x.append(x)
            host_y.append(y)
            host_names.append(node)
            host_hover.append(f"HOST: {node}<br>{label}")
        else:
            switch_x.append(x)
            switch_y.append(y)
            switch_names.append(node)
            switch_hover.append(f"SWITCH: {node}<br>{label}")

    # Hosts Trace (Blue Square)
    fig.add_trace(
        go.Scatter(
            x=host_x,
            y=host_y,
            mode="markers+text",
            marker=dict(symbol="square", size=36, color="#3498db", line=dict(color="#2980b9", width=2)),
            text=host_names,
            textposition="middle center",
            textfont=dict(color="white", size=14, family="Arial Black"),
            hoverinfo="text",
            hovertext=host_hover,
            name="End Hosts",
        )
    )

    # Switches Trace (Purple Circle)
    fig.add_trace(
        go.Scatter(
            x=switch_x,
            y=switch_y,
            mode="markers+text",
            marker=dict(symbol="circle", size=42, color="#9b59b6", line=dict(color="#8e44ad", width=2)),
            text=switch_names,
            textposition="middle center",
            textfont=dict(color="white", size=14, family="Arial Black"),
            hoverinfo="text",
            hovertext=switch_hover,
            name="OpenFlow Switches",
        )
    )

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color="#2c3e50")),
        showlegend=True,
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="#f8f9fa",
        margin=dict(l=20, r=20, t=50, b=20),
        height=380,
    )

    return fig


def create_time_series_plotly_fig(
    time_series_df: pd.DataFrame,
    failure_time: float,
    detection_time: Optional[float] = None,
    title: str = "Packet Delivery & Loss Over Time",
) -> go.Figure:
    """
    Renders an interactive time-series chart showing packets delivered vs dropped per time bin,
    with explicit vertical annotation markers for Failure and Recovery.
    """
    fig = go.Figure()

    if not time_series_df.empty:
        fig.add_trace(
            go.Bar(
                x=time_series_df["time"],
                y=time_series_df["delivered"],
                name="Delivered Packets",
                marker_color="#2ecc71",
            )
        )
        fig.add_trace(
            go.Bar(
                x=time_series_df["time"],
                y=time_series_df["dropped"],
                name="Dropped Packets",
                marker_color="#e74c3c",
            )
        )

    # Failure Injection Vertical Line
    fig.add_vline(
        x=failure_time,
        line_width=2,
        line_dash="dash",
        line_color="#e74c3c",
        annotation_text="Fault Injected",
        annotation_position="top left",
    )

    # Recovery Event Vertical Line
    if detection_time is not None:
        fig.add_vline(
            x=detection_time,
            line_width=2,
            line_dash="dash",
            line_color="#27ae60",
            annotation_text="Fault Detected / Rerouted",
            annotation_position="top right",
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=15)),
        barmode="group",
        xaxis_title="Simulation Time (Units)",
        yaxis_title="Packets per Interval",
        plot_bgcolor="#ffffff",
        margin=dict(l=40, r=20, t=50, b=40),
        height=340,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def save_all_experiment_plots(time_series_df: pd.DataFrame, output_dir: Path, failure_time: float) -> None:
    """Saves static Matplotlib figures for academic reports and docs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if time_series_df.empty:
        return

    # Plot 1: Delivered vs Dropped Packets
    plt.figure(figsize=(9, 4.5))
    plt.bar(time_series_df["time"] - 0.2, time_series_df["delivered"], width=0.4, label="Delivered", color="#2ecc71")
    plt.bar(time_series_df["time"] + 0.2, time_series_df["dropped"], width=0.4, label="Dropped", color="#e74c3c")
    plt.axvline(x=failure_time, color="red", linestyle="--", linewidth=1.5, label="Failure Injected")
    plt.xlabel("Simulation Time Units")
    plt.ylabel("Packet Count")
    plt.title("Traffic Trajectory Before, During, and After Link Failure")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_dir / "packet_trajectory.png", dpi=300)
    plt.close()

    # Plot 2: PDR Over Time
    plt.figure(figsize=(9, 4.5))
    plt.plot(time_series_df["time"], time_series_df["pdr"], marker="o", color="#3498db", linewidth=2, label="PDR (%)")
    plt.axvline(x=failure_time, color="red", linestyle="--", linewidth=1.5, label="Failure Injected")
    plt.xlabel("Simulation Time Units")
    plt.ylabel("Packet Delivery Ratio (%)")
    plt.ylim(-5, 105)
    plt.title("Packet Delivery Ratio (PDR) Dynamic Response")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_dir / "pdr_response.png", dpi=300)
    plt.close()
