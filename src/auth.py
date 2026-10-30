"""Authentication and the public landing page for RORA."""
from pathlib import Path

import bcrypt
import streamlit as st

BASE_DIR = Path(__file__).parent.parent
LOGO_PATH = BASE_DIR / "logo.png"
MAX_FAILED_ATTEMPTS = 5

# Evaluation accounts. Only bcrypt hashes are stored; credentials are shared
# privately with evaluators and are never rendered in the interface.
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
    """Returns {"username", "role"} for valid credentials, otherwise None."""
    if not username or not password:
        return None
    key = username.strip().lower()
    record = USERS.get(key)
    if record and verify_password(password, record["password_hash"]):
        return {"username": key, "role": record["role"]}
    return None


def get_current_user():
    if st.session_state.get("authenticated", False):
        return st.session_state.get("user")
    return None


def logout():
    st.session_state["authenticated"] = False
    st.session_state["user"] = None
    st.rerun()


def render_login_page():
    _, center, _ = st.columns([1, 1.1, 1])
    with center:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), width=150)
        else:
            st.markdown("## RORA")
        st.markdown("### Sign in")

        failed = st.session_state.get("failed_attempts", 0)
        with st.form("login_form", clear_on_submit=False):
            username_input = st.text_input("Username", autocomplete="username")
            password_input = st.text_input("Password", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("Sign in")

        if submitted:
            if failed >= MAX_FAILED_ATTEMPTS:
                st.error("Too many failed attempts. Refresh the page to try again.")
            else:
                info = login(username_input, password_input)
                if info:
                    st.session_state.update(authenticated=True, user=info, failed_attempts=0)
                    st.rerun()
                st.session_state["failed_attempts"] = failed + 1
                st.error("Invalid username or password.")