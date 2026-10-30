import streamlit as st

BRAND = "#3B5B8C"
BRAND_DARK = "#243B5E"

CSS = """
<style>
/* Hide Streamlit chrome but keep the header so the sidebar toggle works on phones */
#MainMenu {visibility: hidden; display: none;}
footer {visibility: hidden; display: none;}
[data-testid="stToolbar"] {visibility: hidden; display: none;}
[data-testid="stDecoration"] {display: none;}
[data-testid="stSidebarNav"] {display: none !important;}
header[data-testid="stHeader"] {background: transparent;}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #1F2933;
}
.block-container {padding-top: 2rem; max-width: 1280px;}

/* Sidebar */
[data-testid="stSidebar"] {background-color: #F8F9FA !important; border-right: 1px solid #E5E7EB !important;}
[data-testid="stSidebar"] div.stPageLink a {
    border-radius: 4px; padding: 0.45rem 0.75rem; color: #1F2933;
    font-weight: 500; text-decoration: none; transition: background-color 0.1s ease;
}
[data-testid="stSidebar"] div.stPageLink a:hover {background-color: #ECEEF2; color: #3B5B8C;}

/* Metrics */
[data-testid="stMetric"] {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px;
    padding: 14px 18px; box-shadow: 0 1px 2px rgba(31, 41, 51, 0.04);
}
[data-testid="stMetricLabel"] {font-size: 0.83rem !important; color: #52606D !important; font-weight: 500 !important;}
[data-testid="stMetricValue"] {font-size: 1.6rem !important; color: #1F2933 !important; font-weight: 650 !important;}

/* Buttons */
div.stButton > button, div[data-testid="stFormSubmitButton"] > button, div.stDownloadButton > button {
    background-color: #3B5B8C; color: #FFFFFF; border: 1px solid #3B5B8C; border-radius: 6px;
    font-size: 0.92rem; font-weight: 500; padding: 0.45rem 1rem; transition: background-color 0.15s ease-in-out;
}
div.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover, div.stDownloadButton > button:hover {
    background-color: #2F4970; border-color: #2F4970; color: #FFFFFF;
}

/* Tabs */
button[data-baseweb="tab"] {font-weight: 600;}

/* Hero header */
.hero {
    background: linear-gradient(120deg, #243B5E 0%, #3B5B8C 100%);
    color: #FFFFFF; border-radius: 10px; padding: 1.5rem 1.75rem; margin-bottom: 1.25rem;
}
.hero .eyebrow {font-size: 0.74rem; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.8; font-weight: 600;}
.hero h1 {color: #FFFFFF; font-size: 1.75rem; line-height: 1.25; margin: 0.25rem 0 0.5rem 0; padding: 0;}
.hero .hero-question {font-size: 1.05rem; font-weight: 600; margin: 0 0 0.35rem 0; color: #FFFFFF;}
.hero p {margin: 0; opacity: 0.92; font-size: 0.95rem; line-height: 1.5; color: #FFFFFF;}

/* Cards and callouts */
.info-card {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px;
    padding: 0.9rem 1.1rem; margin-bottom: 0.9rem; height: 100%;
}
.info-card .info-title {
    font-size: 0.74rem; letter-spacing: 0.06em; text-transform: uppercase;
    color: #3B5B8C; font-weight: 700; margin-bottom: 0.45rem;
}
.info-card .kv {display: flex; justify-content: space-between; gap: 0.75rem; padding: 0.18rem 0; font-size: 0.88rem;}
.info-card .kv span {color: #52606D;}
.info-card .kv b {text-align: right;}

.callout {
    background: #F4F7FB; border: 1px solid #D9E2EC; border-left: 4px solid #3B5B8C;
    border-radius: 6px; padding: 0.8rem 1rem; margin: 0.25rem 0 1rem 0; font-size: 0.92rem; line-height: 1.5;
}
.callout .callout-title {font-weight: 700; margin-bottom: 0.2rem; color: #243B5E;}
.callout.warn {background: #FFF8F0; border-color: #F3D9BE; border-left-color: #DD6B20;}
.callout.warn .callout-title {color: #9C4A0E;}

.role-grid {display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: 0.75rem; margin: 0.5rem 0 1rem 0;}
.role-card {background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 8px; padding: 0.85rem 1rem;}
.role-card .role-name {font-weight: 700; color: #243B5E; margin-bottom: 0.2rem;}
.role-card .role-text {font-size: 0.86rem; color: #52606D; line-height: 1.45;}

.login-card {background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px; padding: 1.25rem 1.5rem 0.25rem 1.5rem; margin-bottom: 0.75rem;}

.user-profile-badge {background: #ECEEF2; border: 1px solid #D2D6DC; border-radius: 6px; padding: 0.5rem 0.7rem; margin-bottom: 0.75rem;}
.user-profile-badge .user-name {font-weight: 600; font-size: 0.9rem; color: #1F2933;}
.user-profile-badge .user-role {font-size: 0.76rem; color: #3B5B8C; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;}
.user-profile-badge .user-scope {font-size: 0.72rem; color: #52606D; margin-top: 2px;}

hr {margin: 1.25rem 0; border-color: #E5E7EB;}

/* Small screens */
@media (max-width: 768px) {
    .block-container {padding-left: 1rem; padding-right: 1rem; padding-top: 1.25rem;}
    .hero {padding: 1.1rem 1.1rem;}
    .hero h1 {font-size: 1.35rem;}
    [data-testid="stMetricValue"] {font-size: 1.3rem !important;}
}
</style>
"""


def apply_style():
    """Injects the shared stylesheet. Brand colour is #3B5B8C."""
    st.markdown(CSS, unsafe_allow_html=True)