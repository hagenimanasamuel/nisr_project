import streamlit as st
import bcrypt
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LOGO_PATH = BASE_DIR / "logo.png"

# Mock accounts with bcrypt-hashed passwords
USERS = {
    "planner": {
        "password_hash": "$2b$12$mPmJ0AQwoAjzFuiyJWMq1uNjJFnJKavvgoeQcSm44bImOWDqMEkr6",
        "role": "planner",
    },
    "school": {
        "password_hash": "$2b$12$fRCwQu5omy/bGatJIz83g.A3NoRxqj/2M74cx2zBDKbuQ2nHHrQ0K",
        "role": "school_staff",
    },
    "analyst": {
        "password_hash": "$2b$12$qjwX73GI01BbTVHXkkVbUeZPJPGaB0fR5QSb1F72USzAfwqdJeBoG",
        "role": "analyst",
    },
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def login(username: str, password: str):
    """
    Validates user credentials against bcrypt hashes.
    Returns a dict with username and role, or None.
    """
    if not username or not password:
        return None
    username_key = username.strip().lower()
    record = USERS.get(username_key)
    if not record:
        return None
    if verify_password(password, record["password_hash"]):
        return {
            "username": username_key,
            "role": record["role"],
        }
    return None


def get_current_user():
    """Returns the current authenticated user dict or None."""
    if st.session_state.get("authenticated", False):
        return st.session_state.get("user")
    return None


def logout():
    """Logs out the user and clears session state."""
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()


def render_login_page():
    """Renders the centered login card."""
    _, center_col, _ = st.columns([1, 1.4, 1])

    with center_col:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)

        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=180)
        else:
            st.markdown("<h2 class='login-title'>RORA</h2>", unsafe_allow_html=True)

        st.markdown("### Sign in")
        st.caption("Education data analysis and early intervention system for Rwanda.")

        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("Username", placeholder="e.g. planner, school, analyst")
            password_input = st.text_input("Password", type="password", placeholder="Enter your password")
            submit_btn = st.form_submit_button("Sign in", use_container_width=True)

            if submit_btn:
                user_info = login(username_input, password_input)
                if user_info:
                    st.session_state["authenticated"] = True
                    st.session_state["user"] = user_info
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please check your credentials.")

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='credentials-box'>", unsafe_allow_html=True)
        st.markdown("**Accounts for evaluation**")
        st.markdown(
            """
- **planner** / `planner123` (Role: National Planner)
- **school** / `school123` (Role: School Staff with intervention form)
- **analyst** / `analyst123` (Role: Policy Analyst)
"""
        )
        st.markdown("</div>", unsafe_allow_html=True)
