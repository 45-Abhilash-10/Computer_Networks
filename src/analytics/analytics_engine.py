"""
analytics_engine.py - Visualizations and comparative analytics for SDN simulation.

Builds interactive Plotly diagrams for the Streamlit dashboard and saves
publication-quality Matplotlib figures for reporting and project evaluation.
Features modern Cyber-NOC dark mode aesthetics, dynamic graph rendering, and
instantaneous network state visualization.
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
    title: str = "SDN Network Fabric State",
    dark_mode: bool = True,
) -> go.Figure:
    """
    Renders an interactive high-contrast 2D network graph in Plotly.
    Distinguishes between Hosts and Switches, dynamically traces active forwarding paths,
    and visually flags severed links with glowing alert aesthetics.
    """
    pos = topology_manager.get_node_positions()
    graph = topology_manager.get_graph()

    # Route edge set for O(1) lookup
    route_edges = set()
    route_nodes = set(active_route) if active_route else set()
    if active_route and len(active_route) > 1:
        for i in range(len(active_route) - 1):
            route_edges.add(tuple(sorted((active_route[i], active_route[i + 1]))))

    failed_pair = tuple(sorted(failed_link)) if failed_link else None

    fig = go.Figure()

    bg_color = "#0b1120" if dark_mode else "#ffffff"
    text_color = "#f8fafc" if dark_mode else "#0f172a"
    inactive_link_color = "rgba(71, 85, 105, 0.45)" if dark_mode else "rgba(148, 163, 184, 0.6)"
    active_link_color = "#10b981"  # Emerald green glow
    failed_link_color = "#ef4444"  # Crimson alert

    # 1. Draw Links (Edges)
    for u, v, data in graph.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_pair = tuple(sorted((u, v)))
        status = data.get("status", "UP")

        if edge_pair == failed_pair or status == "DOWN":
            line_color = failed_link_color
            line_width = 4.5
            line_dash = "dash"
            hover_text = f"<b>CRITICAL FAULT: {u} ──X── {v}</b><br>Status: SEVERED (DOWN)<br>Packets: DROPPED"
        elif edge_pair in route_edges:
            line_color = active_link_color
            line_width = 5.5
            line_dash = "solid"
            hover_text = f"<b>ACTIVE PATH: {u} ──> {v}</b><br>Bandwidth: {data.get('bandwidth')} Mbps<br>Delay: {data.get('delay')} units"
        else:
            line_color = inactive_link_color
            line_width = 2.0
            line_dash = "solid"
            hover_text = f"<b>Link: {u} ── {v}</b><br>Cost: {data.get('cost')}<br>Status: {status}"

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
    host_x, host_y, host_names, host_hover, host_colors = [], [], [], [], []
    switch_x, switch_y, switch_names, switch_hover, switch_colors, switch_borders = [], [], [], [], [], []

    for node, data in graph.nodes(data=True):
        x, y = pos[node]
        node_type = data.get("type", "switch")
        label = data.get("label", node)
        is_in_route = node in route_nodes

        if node_type == "host":
            host_x.append(x)
            host_y.append(y)
            host_names.append(node)
            host_hover.append(f"<b>END HOST: {node}</b><br>{label}<br>Role: Traffic Endpoint")
            host_colors.append("#0284c7")  # Sky Blue
        else:
            switch_x.append(x)
            switch_y.append(y)
            switch_names.append(node)
            deg = graph.degree(node)
            sw_status = "In Forwarding Route" if is_in_route else "Standby Switch"
            switch_hover.append(f"<b>SDN SWITCH: {node}</b><br>{label}<br>Degree: {deg} ports<br>Status: {sw_status}")

            if is_in_route:
                switch_colors.append("#8b5cf6")  # Neon Violet
                switch_borders.append("#10b981")  # Emerald border glow
            else:
                switch_colors.append("#6366f1")  # Indigo
                switch_borders.append("#475569")  # Slate border

    # Draw Switches
    fig.add_trace(
        go.Scatter(
            x=switch_x,
            y=switch_y,
            mode="markers+text",
            marker=dict(
                symbol="circle",
                size=38,
                color=switch_colors,
                line=dict(color=switch_borders, width=3),
            ),
            text=switch_names,
            textposition="middle center",
            textfont=dict(color="#ffffff", size=13, family="JetBrains Mono, monospace"),
            hoverinfo="text",
            hovertext=switch_hover,
            name="SDN Switches",
        )
    )

    # Draw End Hosts
    fig.add_trace(
        go.Scatter(
            x=host_x,
            y=host_y,
            mode="markers+text",
            marker=dict(
                symbol="square",
                size=34,
                color=host_colors,
                line=dict(color="#38bdf8", width=2.5),
            ),
            text=host_names,
            textposition="middle center",
            textfont=dict(color="#ffffff", size=13, family="JetBrains Mono, monospace"),
            hoverinfo="text",
            hovertext=host_hover,
            name="End Hosts",
        )
    )

    # If there is a failed link, place a glowing 'X' marker at the midpoint
    if failed_pair:
        u, v = failed_pair
        if u in pos and v in pos:
            mx = (pos[u][0] + pos[v][0]) / 2.0
            my = (pos[u][1] + pos[v][1]) / 2.0
            fig.add_trace(
                go.Scatter(
                    x=[mx],
                    y=[my],
                    mode="markers+text",
                    marker=dict(symbol="x", size=22, color="#ef4444", line=dict(width=3, color="#ffffff")),
                    text=["FAULT"],
                    textposition="top center",
                    textfont=dict(color="#ef4444", size=11, family="Inter, sans-serif"),
                    hoverinfo="text",
                    hovertext=f"Physical Fault Point: Link {u} ──X── {v}",
                    name="Fault Point",
                    showlegend=False,
                )
            )

    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=text_color, family="Inter, sans-serif")),
        showlegend=True,
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        margin=dict(l=15, r=15, t=45, b=15),
        height=380,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=text_color, size=11),
        ),
    )

    return fig


def create_time_series_plotly_fig(
    time_series_df: pd.DataFrame,
    failure_time: float,
    detection_time: Optional[float] = None,
    title: str = "Packet Delivery & Loss Dynamics",
    dark_mode: bool = True,
) -> go.Figure:
    """Renders cyber-themed time-series chart showing delivered vs dropped packets."""
    bg_color = "#0b1120" if dark_mode else "#ffffff"
    text_color = "#f8fafc" if dark_mode else "#0f172a"
    grid_color = "rgba(51, 65, 85, 0.4)" if dark_mode else "#e2e8f0"

    fig = go.Figure()

    if not time_series_df.empty:
        fig.add_trace(
            go.Bar(
                x=time_series_df["time"],
                y=time_series_df["delivered"],
                name="Delivered Packets",
                marker_color="#10b981",
            )
        )
        fig.add_trace(
            go.Bar(
                x=time_series_df["time"],
                y=time_series_df["dropped"],
                name="Dropped Packets",
                marker_color="#ef4444",
            )
        )

    fig.add_vline(
        x=failure_time,
        line_width=2,
        line_dash="dash",
        line_color="#ef4444",
        annotation_text="Link Severed",
        annotation_position="top left",
        annotation_font=dict(color="#ef4444", size=11),
    )

    if detection_time is not None:
        fig.add_vline(
            x=detection_time,
            line_width=2,
            line_dash="dash",
            line_color="#10b981",
            annotation_text="Fault Rerouted",
            annotation_position="top right",
            annotation_font=dict(color="#10b981", size=11),
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color=text_color, family="Inter, sans-serif")),
        barmode="group",
        xaxis=dict(title="Simulation Time (Units)", color=text_color, gridcolor=grid_color),
        yaxis=dict(title="Packets per Interval", color=text_color, gridcolor=grid_color),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        margin=dict(l=35, r=15, t=45, b=35),
        height=320,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=text_color, size=11),
        ),
    )
    return fig


def save_all_experiment_plots(time_series_df: pd.DataFrame, output_dir: Path, failure_time: float) -> None:
    """Saves static Matplotlib figures for academic reports and docs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    if time_series_df.empty:
        return

    plt.figure(figsize=(9, 4.5))
    plt.bar(time_series_df["time"] - 0.2, time_series_df["delivered"], width=0.4, label="Delivered", color="#10b981")
    plt.bar(time_series_df["time"] + 0.2, time_series_df["dropped"], width=0.4, label="Dropped", color="#ef4444")
    plt.axvline(x=failure_time, color="#ef4444", linestyle="--", linewidth=1.5, label="Failure Injected")
    plt.xlabel("Simulation Time Units")
    plt.ylabel("Packet Count")
    plt.title("Traffic Trajectory Before, During, and After Link Failure")
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_dir / "packet_trajectory.png", dpi=300)
    plt.close()


def create_noc_topology_fig(
    topology_manager: TopologyManager,
    active_route: Optional[List[str]] = None,
    failed_link: Optional[Tuple[str, str]] = None,
    height: int = 240,
    dark_mode: bool = False,
) -> go.Figure:
    """
    Ultra-compact 2D topology figure styled with the user's custom palette:
    - Primary Active Color: #8A6B9E / #B8A3C7 (Muted Dusty Lilac - Palette Bottom Color)
    - Fault / Disrupted Color: #E49678 (Warm Terracotta)
    - Canvas Background: #FDF9F9 (Light) or #16121C (Dark)
    """
    pos = topology_manager.get_node_positions()
    graph = topology_manager.get_graph()

    route_edges = set()
    route_nodes = set(active_route) if active_route else set()
    if active_route and len(active_route) > 1:
        for i in range(len(active_route) - 1):
            route_edges.add(tuple(sorted((active_route[i], active_route[i + 1]))))

    failed_pair = tuple(sorted(failed_link)) if failed_link else None

    # Palette tokens
    if dark_mode:
        bg_color = "#16121c"
        inactive_color = "rgba(115, 96, 124, 0.45)"
        active_color = "#b8a3c7"      # The bottom swatch (Lilac)
        failed_color = "#e49678"      # Terracotta
        text_color = "#fbefef"
        switch_fill = "#231c2c"
        switch_border = "#b8a3c7"
        host_color = "#a084b3"
    else:
        bg_color = "#f4f8fd"         # Lightest shade of blue
        inactive_color = "#c8d8e8"   # Cool soft slate-blue
        active_color = "#8a6b9e"     # Deepened bottom swatch (Lilac)
        failed_color = "#e49678"     # Terracotta
        text_color = "#1e293b"       # Deep slate navy
        switch_fill = "#8a6b9e"      # Lilac
        switch_border = "#6e4f84"
        host_color = "#47617d"       # Steel slate blue

    fig = go.Figure()

    # Draw Edges
    for u, v, data in graph.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_pair = tuple(sorted((u, v)))
        status = data.get("status", "UP")

        if edge_pair == failed_pair or status == "DOWN":
            line_color = failed_color
            line_width = 3.5
            line_dash = "dash"
            hover_text = f"<b>CRITICAL FAULT: {u} ──X── {v}</b><br>Status: SEVERED (DOWN)"
        elif edge_pair in route_edges:
            line_color = active_color
            line_width = 4.5
            line_dash = "solid"
            hover_text = f"<b>ACTIVE PATH: {u} ──> {v}</b><br>Status: FORWARDING"
        else:
            line_color = inactive_color
            line_width = 2.0
            line_dash = "solid"
            hover_text = f"Link: {u} ── {v}<br>Status: {status}"

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

    # Draw Nodes
    host_x, host_y, host_names = [], [], []
    switch_x, switch_y, switch_names, switch_colors, switch_borders = [], [], [], [], []

    for node, data in graph.nodes(data=True):
        x, y = pos[node]
        node_type = data.get("type", "switch")
        is_in_route = node in route_nodes

        if node_type == "host":
            host_x.append(x)
            host_y.append(y)
            host_names.append(node)
        else:
            switch_x.append(x)
            switch_y.append(y)
            switch_names.append(node)
            if is_in_route:
                switch_colors.append(active_color)
                switch_borders.append("#593f6b" if not dark_mode else "#fbefef")
            else:
                switch_colors.append("#b8a3c7" if not dark_mode else "#2e2539")
                switch_borders.append("#8a6b9e" if not dark_mode else "#554366")

    # Switches (Circles)
    fig.add_trace(
        go.Scatter(
            x=switch_x,
            y=switch_y,
            mode="markers+text",
            marker=dict(
                symbol="circle",
                size=32,
                color=switch_colors,
                line=dict(color=switch_borders, width=2.5),
            ),
            text=switch_names,
            textposition="middle center",
            textfont=dict(color="#ffffff", size=11, family="JetBrains Mono, monospace", weight=700),
            hoverinfo="text",
            hovertext=[f"SDN Switch: {n}" for n in switch_names],
            showlegend=False,
        )
    )

    # Hosts (Squares)
    fig.add_trace(
        go.Scatter(
            x=host_x,
            y=host_y,
            mode="markers+text",
            marker=dict(
                symbol="square",
                size=28,
                color=host_color,
                line=dict(color="#ffffff", width=2),
            ),
            text=host_names,
            textposition="middle center",
            textfont=dict(color="#ffffff", size=11, family="JetBrains Mono, monospace", weight=700),
            hoverinfo="text",
            hovertext=[f"Host: {n}" for n in host_names],
            showlegend=False,
        )
    )

    # Midpoint 'X' for failed link
    if failed_pair:
        u, v = failed_pair
        if u in pos and v in pos:
            mx = (pos[u][0] + pos[v][0]) / 2.0
            my = (pos[u][1] + pos[v][1]) / 2.0
            fig.add_trace(
                go.Scatter(
                    x=[mx],
                    y=[my],
                    mode="markers+text",
                    marker=dict(symbol="x", size=18, color=failed_color, line=dict(width=3, color="#ffffff")),
                    text=["FAULT"],
                    textposition="top center",
                    textfont=dict(color=failed_color, size=9, family="Inter, sans-serif", weight=700),
                    hoverinfo="text",
                    hovertext=f"Physical Fault: {u} ──X── {v}",
                    showlegend=False,
                )
            )

    fig.update_layout(
        showlegend=False,
        hovermode="closest",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        margin=dict(l=10, r=10, t=10, b=10),
        height=height,
    )
    return fig


def create_noc_performance_fig(
    time_series_df: pd.DataFrame,
    failure_time: float,
    recovery_time: Optional[float] = None,
    height: int = 125,
    dark_mode: bool = False,
) -> go.Figure:
    """
    Compact multi-line/area timeline chart styled with the user's custom palette.
    """
    fig = go.Figure()

    if dark_mode:
        bg_color = "#16121c"
        grid_color = "rgba(75, 60, 85, 0.3)"
        deliv_color = "#b8a3c7"      # Bottom color
        deliv_fill = "rgba(184, 163, 199, 0.25)"
        drop_color = "#e49678"       # Terracotta
        drop_fill = "rgba(228, 150, 120, 0.3)"
        text_color = "#9e8ba8"
    else:
        bg_color = "#f4f8fd"         # Lightest shade of blue
        grid_color = "rgba(180, 205, 230, 0.45)"
        deliv_color = "#8a6b9e"      # Bottom color (contrast)
        deliv_fill = "rgba(184, 163, 199, 0.35)"
        drop_color = "#e49678"       # Terracotta
        drop_fill = "rgba(228, 150, 120, 0.3)"
        text_color = "#5c728e"

    if not time_series_df.empty:
        # Delivered Area (The Bottom Palette Color)
        fig.add_trace(
            go.Scatter(
                x=time_series_df["time"],
                y=time_series_df["delivered"],
                mode="lines",
                name="Delivered",
                line=dict(color=deliv_color, width=2.5),
                fill="tozeroy",
                fillcolor=deliv_fill,
            )
        )
        # Dropped Area (Terracotta)
        fig.add_trace(
            go.Scatter(
                x=time_series_df["time"],
                y=time_series_df["dropped"],
                mode="lines",
                name="Dropped",
                line=dict(color=drop_color, width=2),
                fill="tozeroy",
                fillcolor=drop_fill,
            )
        )

    # Vertical Fault and Recovery lines
    fig.add_vline(
        x=failure_time,
        line_width=1.5,
        line_dash="dash",
        line_color=drop_color,
        annotation_text="FAULT",
        annotation_position="top left",
        annotation_font=dict(color=drop_color, size=9),
    )

    if recovery_time is not None:
        fig.add_vline(
            x=recovery_time,
            line_width=1.5,
            line_dash="dash",
            line_color=deliv_color,
            annotation_text="HEALED",
            annotation_position="top right",
            annotation_font=dict(color=deliv_color, size=9),
        )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=text_color, size=9),
        ),
        xaxis=dict(
            title="",
            showgrid=True,
            gridcolor=grid_color,
            color=text_color,
            tickfont=dict(size=9),
        ),
        yaxis=dict(
            title="",
            showgrid=True,
            gridcolor=grid_color,
            color=text_color,
            tickfont=dict(size=9),
        ),
        paper_bgcolor=bg_color,
        plot_bgcolor=bg_color,
        margin=dict(l=25, r=10, t=10, b=20),
        height=height,
    )
    return fig
