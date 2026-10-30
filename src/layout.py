"""Shared sidebar for every authenticated page."""
import os
from pathlib import Path

import streamlit as st

from src.auth import USERS, get_current_user, logout

BASE_DIR = Path(__file__).parent.parent
LOGO_PATH = BASE_DIR / "logo.png"

ROLE_TITLES = {
    "planner": "National Planner",
    "school_staff": "School Staff",
    "analyst": "Policy Analyst",
}
ROLE_SCOPES = {
    "planner": "National resource allocation",
    "school_staff": "Student case management",
    "analyst": "Analytics and model diagnostics",
}
SWITCHER_LABELS = {
    "planner": "National Planner",
    "analyst": "Policy Analyst",
    "school": "School Staff",
}

# Evaluators can preview every role without signing out. Set RORA_ROLE_SWITCHER=0
# in the environment to disable this for a production deployment.
ROLE_SWITCHER_ENABLED = os.environ.get("RORA_ROLE_SWITCHER", "1") != "0"


def render_sidebar(current_page: str = "Home"):
    user = get_current_user()
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=150)
        else:
            st.markdown("### RORA")
        st.caption("NISR Big Data Hackathon 2026")
        st.divider()

        if not user:
            return

        role_key = user.get("role", "")
        username = user.get("username", "")
        st.markdown(
            f'<div class="user-profile-badge"><div class="user-name">{username}</div>'
            f'<div class="user-role">{ROLE_TITLES.get(role_key, role_key)}</div>'
            f'<div class="user-scope">{ROLE_SCOPES.get(role_key, "")}</div></div>',
            unsafe_allow_html=True,
        )

        st.caption("NAVIGATION")
        st.page_link("app.py", label="Dashboard", icon=":material/dashboard:")
        st.page_link("pages/2_Early_Intervention.py", label="Early intervention", icon=":material/flag:")
        st.divider()

        if ROLE_SWITCHER_ENABLED:
            st.caption("PREVIEW ANOTHER ROLE")
            keys = list(SWITCHER_LABELS)
            choice = st.selectbox(
                "Role preview",
                keys,
                index=keys.index(username) if username in keys else 0,
                format_func=SWITCHER_LABELS.get,
                label_visibility="collapsed",
            )
            if choice != username:
                st.session_state["user"] = {"username": choice, "role": USERS[choice]["role"]}
                st.rerun()
            st.divider()

        if st.button("Log out"):
            logout()