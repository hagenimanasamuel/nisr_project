import streamlit as st


def apply_style():
    """
    Injects professional CSS for the RORA application.
    Enforces brand color #3B5B8C, calm cards, clean typography,
    and removes standard Streamlit toolbars and default navigation.
    """
    css = """
    <style>
    /* Hide Streamlit default chrome and toolbar */
    #MainMenu {visibility: hidden; display: none;}
    footer {visibility: hidden; display: none;}
    header[data-testid="stHeader"] {visibility: hidden; height: 0px;}
    [data-testid="stToolbar"] {visibility: hidden; display: none;}
    [data-testid="stSidebarNav"] {display: none !important;}

    /* Root typography and background */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        color: #1F2933;
    }

    /* Professional sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #F8F9FA !important;
        border-right: 1px solid #E5E7EB !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.25rem;
        padding-bottom: 1.5rem;
    }

    /* Calm metric cards with light border and no heavy shadows */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 14px 18px;
        box-shadow: none;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        color: #52606D !important;
        font-weight: 500 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.65rem !important;
        color: #1F2933 !important;
        font-weight: 600 !important;
    }

    /* Primary buttons styled with brand color #3B5B8C */
    div.stButton > button,
    div[data-testid="stFormSubmitButton"] > button {
        background-color: #3B5B8C;
        color: #FFFFFF;
        border: 1px solid #3B5B8C;
        border-radius: 4px;
        font-size: 0.92rem;
        font-weight: 500;
        padding: 0.45rem 1rem;
        transition: background-color 0.15s ease-in-out;
    }
    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {
        background-color: #2F4970;
        border-color: #2F4970;
        color: #FFFFFF;
    }
    div.stButton > button:focus,
    div[data-testid="stFormSubmitButton"] > button:focus {
        border-color: #2F4970;
        box-shadow: 0 0 0 2px rgba(59, 91, 140, 0.2);
    }

    /* Page links in sidebar */
    [data-testid="stSidebar"] div.stPageLink a {
        border-radius: 4px;
        padding: 0.45rem 0.75rem;
        color: #1F2933;
        font-weight: 500;
        text-decoration: none;
        transition: background-color 0.1s ease;
    }
    [data-testid="stSidebar"] div.stPageLink a:hover {
        background-color: #ECEEF2;
        color: #3B5B8C;
    }

    /* Card styling for forms and containers */
    .login-card {
        background: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 2rem;
        margin-top: 1.5rem;
        margin-bottom: 1.25rem;
    }
    .credentials-box {
        background: #F8F9FA;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 1rem 1.25rem;
        font-size: 0.88rem;
        color: #52606D;
        margin-bottom: 1.5rem;
    }
    .user-profile-badge {
        background-color: #ECEEF2;
        border: 1px solid #D2D6DC;
        border-radius: 4px;
        padding: 0.4rem 0.65rem;
        margin-bottom: 0.75rem;
    }
    .user-profile-badge .user-name {
        font-weight: 600;
        font-size: 0.9rem;
        color: #1F2933;
    }
    .user-profile-badge .user-role {
        font-size: 0.78rem;
        color: #3B5B8C;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Clean divider line */
    hr {
        margin: 1.25rem 0;
        border-color: #E5E7EB;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
