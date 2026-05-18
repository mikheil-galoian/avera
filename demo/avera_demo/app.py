from __future__ import annotations

import os

import streamlit as st

from .artifacts import DEFAULT_SCENARIO, load_snapshot, list_scenarios_for_track, scenario_paths
from .runner import run_analysis
from .views import render_shell, render_sidebar


def main() -> None:
    st.set_page_config(
        page_title="AVERA Demo Shell",
        page_icon="A",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    preferred = os.environ.get("AVERA_DEFAULT_SCENARIO", DEFAULT_SCENARIO)
    default_track = "adapted" if "adapted" in preferred else "standard"
    track = st.sidebar.radio(
        "Scenario Set",
        ("standard", "adapted", "all"),
        index=("standard", "adapted", "all").index(default_track) if default_track in {"standard", "adapted"} else 0,
        format_func=lambda value: value.title(),
    )

    scenario_names = list_scenarios_for_track(track)
    if not scenario_names:
        st.title("AVERA Demo Shell")
        st.error("No fixture scenarios were found for the selected scenario set.")
        return

    if preferred in scenario_names:
        default_index = scenario_names.index(preferred)
    elif DEFAULT_SCENARIO in scenario_names:
        default_index = scenario_names.index(DEFAULT_SCENARIO)
    else:
        default_index = 0
    selected = st.sidebar.selectbox("Scenario", scenario_names, index=default_index)
    snapshot = load_snapshot(scenario_paths(selected))

    run_requested, refresh_requested = render_sidebar(snapshot)
    if run_requested:
        success, stdout, stderr = run_analysis(snapshot.scenario)
        if success:
            st.sidebar.success("Analysis finished.")
        else:
            st.sidebar.error("Analysis failed.")
        if stdout:
            st.sidebar.code(stdout, language="text")
        if stderr:
            st.sidebar.code(stderr, language="text")
        snapshot = load_snapshot(snapshot.scenario)
    if refresh_requested:
        st.rerun()

    render_shell(snapshot)
