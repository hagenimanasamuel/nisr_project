import streamlit as st
from pathlib import Path
from src.auth import get_current_user, logout, USERS

BASE_DIR = Path(__file__).parent.parent
LOGO_PATH = BASE_DIR / "logo.png"

ROLE_TITLES = {
    "planner": "National Planner",
    "school_staff": "School Staff",
    "analyst": "Policy Analyst",
}

ROLE_SCOPES = {
    "planner": "National Resource Allocation",
    "school_staff": "Student Case Management",
    "analyst": "Multi-Source Analytics & Models",
}


def render_sidebar(current_page: str = "Home"):
    """
    Renders the unified sidebar across all authenticated pages:
    - Logo (or text 'RORA' if logo image is missing)
    - User account info and role badge with specific operational scope
    - Fast role preview switcher for hackathon judges and evaluators
    - Role-based navigation links
    - Logout button
    """
    user = get_current_user()

    with st.sidebar:
        # Logo handling: fallback to text if logo.png is missing
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=150)
        else:
            st.markdown("### RORA")

        st.caption("NISR Big Data Hackathon 2026")
        st.divider()

        if user:
            role_key = user.get("role", "")
            role_display = ROLE_TITLES.get(role_key, role_key.replace("_", " ").title())
            role_scope = ROLE_SCOPES.get(role_key, "Sector Intelligence")
            username = user.get("username", "")

            # User profile card showing distinct role scope
            st.markdown(
                f"""
                <div class="user-profile-badge">
                    <div class="user-name">{username}</div>
                    <div class="user-role">{role_display}</div>
                    <div style="font-size: 0.72rem; color: #52606D; margin-top: 2px;">Scope: {role_scope}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown(
                "<p style='font-size: 0.8rem; font-weight: 600; color: #52606D; margin-bottom: 0.5rem;'>NAVIGATION</p>",
                unsafe_allow_html=True,
            )

            # Navigation links
            try:
                st.page_link("app.py", label="District & Systemic Intelligence", icon="📊")
                st.page_link("pages/2_Early_Intervention.py", label="Early Intervention & Case Management", icon="🎯")
            except Exception:
                pass

            st.divider()

            # Fast Role Switcher for Hackathon Evaluation
            st.markdown(
                "<p style='font-size: 0.75rem; font-weight: 600; color: #52606D; text-transform: uppercase;'>Switch Role View</p>",
                unsafe_allow_html=True,
            )
            role_options = {
                "planner": "National Planner (Resource allocation)",
                "analyst": "Policy Analyst (Model diagnostics)",
                "school": "School Staff (Student intervention form)",
            }
            selected_account = st.selectbox(
                "Active Account",
                options=list(role_options.keys()),
                index=list(role_options.keys()).index(username) if username in role_options else 0,
                format_func=lambda x: role_options[x],
                label_visibility="collapsed",
            )
            if selected_account != username:
                st.session_state["authenticated"] = True
                st.session_state["user"] = {
                    "username": selected_account,
                    "role": USERS[selected_account]["role"],
                }
                st.rerun()

            st.divider()

            if st.button("Log out", use_container_width=True):
                logout()
