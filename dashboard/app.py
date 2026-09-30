"""
app.py - Professional Single-Screen SDN Network Operations Center (NOC) Dashboard.

Designed to fit strictly on one desktop screen (1080p / 768p) without scrolling.
Provides instant visual comprehension of:
1. Physical Network Topology & Link Health
2. Centralized SDN Controller State
3. Active vs Broken vs Recovered Routes
4. Real-time Failure Detection & Rerouting Timings
5. Empirical KPIs (PDR, Loss %, Latency, Throughput, MTTR)
6. Dynamic Before/Failure/Recovery Performance Timeline
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from src.config import SimulationConfig
from src.topology.topology_manager import TopologyManager
from src.simulation.traffic_simulator import TrafficSimulator
from src.analytics.analytics_engine import (
    create_noc_topology_fig,
    create_noc_performance_fig,
)

# 1. Page Configuration
st.set_page_config(
    page_title="SDN Control Center // NOC",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Ultra-Compact High-Contrast NOC CSS Styled with User's Custom Palette
# Palette: #FBEFEF (Canvas), #FFFFFF (Cards), #8A6B9E / #B8A3C7 (Bottom Lilac Accent), #E49678 (Terracotta Fault)
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, sans-serif !important;
        background-color: #fbefef !important;
        color: #2e2137 !important;
    }

    /* Remove default Streamlit whitespace */
    header[data-testid="stHeader"] { display: none !important; }
    footer { display: none !important; }
    #MainMenu { visibility: hidden !important; }

    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0.2rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
        max-width: 100% !important;
    }

    /* Compact NOC Card Containers */
    .noc-box {
        background: #ffffff;
        border: 1px solid #ead8de;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(138, 107, 158, 0.08);
        padding: 7px 12px;
        margin-bottom: 5px;
    }

    .noc-header-tag {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: #8a6b9e;
        margin-bottom: 2px;
    }

    .noc-title {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #6c557b;
        margin-bottom: 4px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* KPI Cards */
    .kpi-card {
        background: #ffffff;
        border: 1px solid #ead8de;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(138, 107, 158, 0.08);
        padding: 6px 10px;
        text-align: left;
    }
    .kpi-label {
        font-size: 10px;
        font-weight: 600;
        color: #766482;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 1px;
    }
    .kpi-val {
        font-family: 'JetBrains Mono', monospace;
        font-size: 19px;
        font-weight: 700;
        color: #8a6b9e;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 10px;
        color: #8e7e98;
        margin-top: 1px;
    }

    /* Status Badges */
    .badge-healthy {
        background: rgba(138, 107, 158, 0.12);
        color: #5d3e73;
        border: 1px solid #b8a3c7;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .badge-fault {
        background: rgba(228, 150, 120, 0.18);
        color: #c85a32;
        border: 1px solid #e49678;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .badge-recovering {
        background: rgba(235, 184, 184, 0.25);
        color: #9e5b6a;
        border: 1px solid #ebb8b8;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .badge-blue {
        background: rgba(184, 163, 199, 0.25);
        color: #5d3e73;
        border: 1px solid #b8a3c7;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 700;
    }

    /* Monospace Route Paths */
    .mono-route {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #5d3e73;
        background: #faf4f6;
        border: 1px solid #ead8de;
        padding: 5px 8px;
        border-radius: 4px;
        margin-top: 2px;
        margin-bottom: 4px;
    }

    /* Primary and Secondary Button Overrides (Lilac Accent) */
    .stButton > button {
        border-radius: 4px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        height: 32px !important;
        letter-spacing: 0.02em !important;
        border: 1px solid #cdbad9 !important;
        background-color: #ffffff !important;
        color: #5d486d !important;
    }
    .stButton > button:hover {
        background-color: #f7eff7 !important;
        border-color: #8a6b9e !important;
        color: #2e2137 !important;
    }
    .stButton > button[kind="primary"] {
        background-color: #8a6b9e !important;
        color: #ffffff !important;
        border: 1px solid #745687 !important;
        box-shadow: 0 1px 3px rgba(138, 107, 158, 0.25) !important;
    }
    .stButton > button[kind="primary"]:hover {
        background-color: #745687 !important;
        border-color: #5d3e73 !important;
    }

    /* Input & Selectbox Overrides */
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div {
        background-color: #ffffff !important;
        border: 1px solid #dccad0 !important;
        color: #2e2137 !important;
        border-radius: 4px !important;
        min-height: 32px !important;
        height: 32px !important;
    }
    div[data-baseweb="select"] span, div[data-baseweb="input"] input {
        color: #2e2137 !important;
        font-size: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def run_simulation_scenario(mode: str = "self_healing", failed_link: tuple = ("S2", "S3"), failure_time: float = 10.0, rate: float = 5.0):
    """Executes the discrete-event simulation and returns the result."""
    tm = TopologyManager()
    cfg = SimulationConfig(
        simulation_duration=30.0,
        packet_rate=rate,
        failure_time=failure_time,
        heartbeat_interval=1.0,
        failed_link=failed_link,
        routing_mode=mode,
    )
    sim = TrafficSimulator(cfg, topology_manager=tm)
    return sim.run(), tm


# 3. Session State Initialization
if "dashboard_state" not in st.session_state:
    # Initial state: run the complete self-healing demo by default
    res, tm = run_simulation_scenario(mode="self_healing", failed_link=("S2", "S3"), failure_time=10.0)
    st.session_state["sim_result"] = res
    st.session_state["topology_mgr"] = tm
    st.session_state["app_mode"] = "RECOVERED"
    st.session_state["target_link"] = ("S2", "S3")

# Simulation controls actions
c_ctrl = st.container()

sim_res = st.session_state["sim_result"]
tm = st.session_state["topology_mgr"]
metrics = sim_res.summary_metrics
app_mode = st.session_state["app_mode"]
rec = sim_res.recovery_record
target_link = st.session_state["target_link"]

# 4. Header Bar
h_left, h_right = st.columns([8, 4])
with h_left:
    st.markdown(
        """
        <div style="display: flex; align-items: baseline; gap: 12px;">
            <span class="noc-header-tag">NETWORK // SDN CONTROL CENTER</span>
            <span style="font-size: 18px; font-weight: 800; color: #2e2137; letter-spacing: -0.01em;">INTELLIGENT SELF-HEALING SDN NETWORK</span>
            <span style="font-size: 11px; color: #766482;">Failure Detection • Dynamic Routing • Automated Recovery</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with h_right:
    if app_mode == "HEALTHY":
        badge_html = "<span class='badge-healthy'>● SYSTEM HEALTHY</span>"
    elif app_mode == "FAULT_ACTIVE":
        badge_html = "<span class='badge-fault'>● LINK FAILURE (UNRECOVERED)</span>"
    else:
        badge_html = "<span class='badge-healthy'>● SYSTEM HEALTHY // RECOVERED</span>"

    st.markdown(f"<div style='text-align: right; padding-top: 2px;'>{badge_html}</div>", unsafe_allow_html=True)

# 5. KPI Section: 5 Compact Cards in 1 Row
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Packet Delivery Ratio</div>
            <div class="kpi-val" style="color: #8a6b9e;">{metrics['pdr_pct']:.1f}%</div>
            <div class="kpi-sub">Delivered: {metrics['packets_received']} / {metrics['packets_sent']} pkts</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k2:
    loss_color = "#8a6b9e" if metrics['packet_loss_pct'] < 15.0 else "#e49678"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Packet Loss</div>
            <div class="kpi-val" style="color: {loss_color};">{metrics['packet_loss_pct']:.1f}%</div>
            <div class="kpi-sub">Dropped: {metrics['packets_lost']} pkts</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Avg End-to-End Delay</div>
            <div class="kpi-val" style="color: #8a6b9e;">{metrics['avg_delay']:.2f} <span style="font-size:12px;">units</span></div>
            <div class="kpi-sub">Min: {metrics['min_delay']:.1f} | Max: {metrics['max_delay']:.1f}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Data Throughput</div>
            <div class="kpi-val" style="color: #2e2137;">{metrics['throughput_kbps']:.1f} <span style="font-size:12px;">kbps</span></div>
            <div class="kpi-sub">{metrics['throughput_pps']:.2f} packets / unit</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with k5:
    rec_time_str = f"{metrics['recovery_time']:.2f} s" if app_mode == "RECOVERED" else ("Failed" if app_mode == "FAULT_ACTIVE" else "N/A")
    rec_val_color = "#8a6b9e" if app_mode == "RECOVERED" else ("#e49678" if app_mode == "FAULT_ACTIVE" else "#766482")
    sub_text = f"Det: {metrics['detection_time']:.1f}s | Reroute: {metrics['reroute_time']:.2f}s" if app_mode == "RECOVERED" else "No Failure Active"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">Total Recovery Time</div>
            <div class="kpi-val" style="color: {rec_val_color};">{rec_time_str}</div>
            <div class="kpi-sub">{sub_text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# 6. Main Grid (Topology + Route Status on Left, Status + Event + Performance on Right)
col_left, col_right = st.columns([7, 5])

with col_left:
    # Network Topology Box
    failed_edge = target_link if app_mode in ("FAULT_ACTIVE", "RECOVERED") else None
    active_path = sim_res.final_route if app_mode == "RECOVERED" else (sim_res.initial_route if app_mode == "HEALTHY" else [])

    st.markdown(
        """
        <div class="noc-box" style="margin-bottom: 2px;">
            <div class="noc-title">
                <span>NETWORK TOPOLOGY // SDN DATA PLANE</span>
                <span style="font-size: 10px; color: #766482;">H1 ── S1 ── [S2 / S4] ── S3 ── H2</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    topo_fig = create_noc_topology_fig(
        topology_manager=tm,
        active_route=active_path,
        failed_link=failed_edge,
        height=240,
        dark_mode=False,
    )
    st.plotly_chart(topo_fig, use_container_width=True, config={"displayModeBar": False})

    # Compact Legend
    st.markdown(
        """
        <div style="display: flex; gap: 14px; font-size: 10px; color: #766482; justify-content: center; margin-top: -6px; margin-bottom: 4px;">
            <span><span style="color:#685f42;">■</span> Host</span>
            <span><span style="color:#b8a3c7;">●</span> Switch</span>
            <span><span style="color:#8a6b9e; font-weight:bold;">━</span> Active Route</span>
            <span><span style="color:#dccad0; font-weight:bold;">━</span> Standby Link</span>
            <span><span style="color:#e49678; font-weight:bold;">━✖</span> Failed Link</span>
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Route / Recovery Status Box
    init_str = " → ".join(sim_res.initial_route) if sim_res.initial_route else "H1 → S1 → S2 → S3 → H2"
    rec_str = " → ".join(sim_res.final_route) if sim_res.final_route else "H1 → S1 → S4 → S5 → S3 → H2"

    if app_mode == "RECOVERED":
        primary_badge = "<span class='badge-fault'>✖ FAILED / INVALID</span>"
        rec_badge = "<span class='badge-healthy'>● ACTIVE FORWARDING</span>"
        rec_color = "#8a6b9e"
    elif app_mode == "FAULT_ACTIVE":
        primary_badge = "<span class='badge-fault'>✖ BROKEN LINK (DROPPING)</span>"
        rec_badge = "<span style='color:#766482; font-size:11px;'>◌ UNRECOVERED</span>"
        rec_color = "#766482"
    else:
        primary_badge = "<span class='badge-healthy'>● ACTIVE FORWARDING</span>"
        rec_badge = "<span style='color:#766482; font-size:11px;'>◌ STANDBY PATH</span>"
        rec_color = "#766482"

    st.markdown(
        f"""
        <div class="noc-box">
            <div class="noc-title">ROUTE / RECOVERY STATUS</div>
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 10px; color: #766482; font-weight: 600;">PRIMARY ROUTE (DIJKSTRA)</span>
                {primary_badge}
            </div>
            <div class="mono-route" style="color: {'#e49678' if app_mode in ('FAULT_ACTIVE', 'RECOVERED') else '#8a6b9e'};">{init_str}</div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
                <span style="font-size: 10px; color: #766482; font-weight: 600;">RECOVERED ALTERNATE ROUTE</span>
                {rec_badge}
            </div>
            <div class="mono-route" style="color: {rec_color}; font-weight: {'700' if app_mode == 'RECOVERED' else '400'};">{rec_str}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_right:
    # Network Status Card
    links_total = len(tm.get_all_links())
    failed_count = 1 if app_mode in ("FAULT_ACTIVE", "RECOVERED") else 0
    active_count = links_total - failed_count

    st.markdown(
        f"""
        <div class="noc-box">
            <div class="noc-title">
                <span>NETWORK STATUS</span>
                <span class="badge-blue">CONTROLLER ● ONLINE</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px 12px; font-size: 11px;">
                <div><span style="color:#766482;">Network Health:</span> <b style="color:{'#8a6b9e' if app_mode != 'FAULT_ACTIVE' else '#e49678'};">{'HEALTHY' if app_mode == 'HEALTHY' else ('DEGRADED' if app_mode == 'FAULT_ACTIVE' else 'RECOVERED')}</b></div>
                <div><span style="color:#766482;">Active Flow:</span> <b style="color:#8a6b9e;">H1 → H2</b></div>
                <div><span style="color:#766482;">Active Links:</span> <b style="color:#2e2137;">{active_count} / {links_total}</b></div>
                <div><span style="color:#766482;">Failed Links:</span> <b style="color:{'#e49678' if failed_count > 0 else '#8a6b9e'};">{failed_count}</b></div>
                <div><span style="color:#766482;">Packets Processed:</span> <b style="color:#2e2137;">{metrics['packets_sent']}</b></div>
                <div><span style="color:#766482;">Control Mode:</span> <b style="color:#2e2137;">{sim_res.config.routing_mode.upper()}</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Failure Event Card
    if app_mode in ("FAULT_ACTIVE", "RECOVERED"):
        f_title = f"<span class='badge-fault'>● LINK FAILURE: {target_link[0]} ── {target_link[1]}</span>"
        f_status_txt = "Autonomous Dijkstra Reroute Installed. Traffic Restored." if app_mode == "RECOVERED" else "Unrecovered Outage (Static Routing In Place)."
        f_status_clr = "#8a6b9e" if app_mode == "RECOVERED" else "#e49678"
        f_details = (
            f'<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 3px 12px; font-size: 11px; margin-top: 4px;">'
            f'<div><span style="color:#766482;">Failure Injected:</span> <b style="color:#2e2137;">{sim_res.config.failure_time:.1f} s</b></div>'
            f'<div><span style="color:#766482;">Detection Time:</span> <b style="color:#2e2137;">{rec.get("detection_time", 11.0):.1f} s</b></div>'
            f'<div><span style="color:#766482;">Reroute Time:</span> <b style="color:#2e2137;">{rec.get("reroute_time", 11.05):.2f} s</b></div>'
            f'<div><span style="color:#766482;">Recovery Latency:</span> <b style="color:#8a6b9e;">{metrics["recovery_time"]:.2f} s</b></div>'
            f'</div>'
            f'<div style="font-size: 10px; color: {f_status_clr}; margin-top: 4px;">'
            f'● <b>Status:</b> {f_status_txt}'
            f'</div>'
        )
    else:
        f_title = "<span class='badge-healthy'>● NO ACTIVE FAILURE</span>"
        f_details = (
            '<div style="font-size: 11px; color: #766482; margin-top: 4px;">'
            'Network operating under normal baseline parameters. All 7 physical links are healthy and passing traffic.'
            '</div>'
        )

    st.markdown(
        f"""
        <div class="noc-box">
            <div class="noc-title">
                <span>FAILURE EVENT TELEMETRY</span>
                {f_title}
            </div>
            {f_details}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Performance Timeline Mini-Chart
    st.markdown(
        """
        <div class="noc-box" style="margin-bottom: 2px;">
            <div class="noc-title">
                <span>PERFORMANCE: [BEFORE] ── [FAILURE] ── [RECOVERY]</span>
                <span style="font-size: 10px; color: #766482;">DELIVERED VS DROPPED</span>
            </div>
        """,
        unsafe_allow_html=True,
    )

    det_time_ts = rec.get("detection_time") if app_mode == "RECOVERED" else None
    fail_time_ts = sim_res.config.failure_time if app_mode in ("FAULT_ACTIVE", "RECOVERED") else 999.0
    perf_fig = create_noc_performance_fig(
        time_series_df=sim_res.time_series_df,
        failure_time=fail_time_ts,
        recovery_time=det_time_ts,
        height=110,
        dark_mode=False,
    )
    st.plotly_chart(perf_fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown("</div>", unsafe_allow_html=True)

# 7. Simulation Control Bar (Bottom Footer Toolbar)
st.markdown("<div style='height: 2px;'></div>", unsafe_allow_html=True)
b_box = st.container()
with b_box:
    c1, c2, c3, c4, c5, c6 = st.columns([2.5, 2.0, 2.0, 2.5, 2.5, 2.0])

    with c1:
        target_link_choice = st.selectbox(
            "Target Link:",
            options=[("S2", "S3"), ("S1", "S2"), ("S4", "S5")],
            format_func=lambda p: f"Link ({p[0]} ── {p[1]})",
            label_visibility="collapsed",
        )
    with c2:
        fail_t = st.number_input("Fault Time:", min_value=5.0, max_value=25.0, value=10.0, step=1.0, label_visibility="collapsed")
    with c3:
        t_rate = st.number_input("Rate (pkts/u):", min_value=1.0, max_value=20.0, value=5.0, step=1.0, label_visibility="collapsed")
    with c4:
        if st.button("▶ RUN SIMULATION", type="primary", use_container_width=True):
            res, tm = run_simulation_scenario(mode="self_healing", failed_link=target_link_choice, failure_time=fail_t, rate=t_rate)
            st.session_state["sim_result"] = res
            st.session_state["topology_mgr"] = tm
            st.session_state["app_mode"] = "RECOVERED"
            st.session_state["target_link"] = target_link_choice
            st.rerun()
    with c5:
        if st.button("⚡ INJECT FAILURE", use_container_width=True):
            # Run in static mode to demonstrate persistent outage
            res, tm = run_simulation_scenario(mode="static", failed_link=target_link_choice, failure_time=fail_t, rate=t_rate)
            st.session_state["sim_result"] = res
            st.session_state["topology_mgr"] = tm
            st.session_state["app_mode"] = "FAULT_ACTIVE"
            st.session_state["target_link"] = target_link_choice
            st.rerun()
    with c6:
        if st.button("↻ RESET", use_container_width=True):
            # Reset to normal healthy network with no failure
            res, tm = run_simulation_scenario(mode="self_healing", failed_link=target_link_choice, failure_time=999.0, rate=t_rate)
            st.session_state["sim_result"] = res
            st.session_state["topology_mgr"] = tm
            st.session_state["app_mode"] = "HEALTHY"
            st.session_state["target_link"] = target_link_choice
            st.rerun()
