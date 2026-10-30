import html

import streamlit as st

BRAND = "#3B5B8C"
TIER_COLORS = {"High Risk": "#C53030", "Moderate Risk": "#DD6B20", "Low Risk": "#3B5B8C"}
TIER_ORDER = ["High Risk", "Moderate Risk", "Low Risk"]
PRIORITY_COLORS = {"Priority 1": "#C53030", "Priority 2": "#DD6B20", "Priority 3": "#8DA2C0"}
PRIORITY_ORDER = ["Priority 1", "Priority 2", "Priority 3"]


def _streamlit_at_least(major: int, minor: int) -> bool:
    try:
        parts = st.__version__.split(".")
        return (int(parts[0]), int(parts[1])) >= (major, minor)
    except Exception:
        return False


# Newer Streamlit replaces use_container_width with width="stretch".
_STRETCH = _streamlit_at_least(1, 50)


def style_figure(fig, height=None):
    """Applies the shared chart look."""
    fig.update_layout(
        font=dict(
            family="-apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif",
            color="#1F2933",
            size=13,
        ),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=10, r=10, t=50, b=40),
        title=dict(font=dict(size=16)),
        legend=dict(orientation="h", yanchor="top", y=-0.12, x=0, title_text=""),
    )
    fig.update_xaxes(gridcolor="#E5E7EB", zeroline=False)
    fig.update_yaxes(gridcolor="#E5E7EB", zeroline=False)
    if height:
        fig.update_layout(height=height)
    return fig


def show_chart(fig, height=None, key=None):
    style_figure(fig, height)
    if _STRETCH:
        st.plotly_chart(fig, width="stretch", key=key)
    else:
        st.plotly_chart(fig, use_container_width=True, key=key)


def show_table(df, column_config=None, height=None):
    kwargs = {"hide_index": True}
    if column_config:
        kwargs["column_config"] = column_config
    if height:
        kwargs["height"] = height
    if _STRETCH:
        kwargs["width"] = "stretch"
    else:
        kwargs["use_container_width"] = True
    st.dataframe(df, **kwargs)


def page_header(eyebrow: str, title: str, question: str, description: str):
    st.markdown(
        '<div class="hero">'
        f'<div class="eyebrow">{html.escape(eyebrow)}</div>'
        f"<h1>{html.escape(title)}</h1>"
        f'<p class="hero-question">{html.escape(question)}</p>'
        f"<p>{html.escape(description)}</p>"
        "</div>",
        unsafe_allow_html=True,
    )


def callout(title: str, body: str, kind: str = "info"):
    """Body may contain simple inline HTML such as <b>."""
    css = "callout warn" if kind == "warn" else "callout"
    st.markdown(
        f'<div class="{css}"><div class="callout-title">{html.escape(title)}</div>{body}</div>',
        unsafe_allow_html=True,
    )


def info_card(title: str, rows):
    body = "".join(
        f'<div class="kv"><span>{html.escape(str(k))}</span><b>{html.escape(str(v))}</b></div>'
        for k, v in rows
    )
    st.markdown(
        f'<div class="info-card"><div class="info-title">{html.escape(title)}</div>{body}</div>',
        unsafe_allow_html=True,
    )


def kpi_row(items):
    """items: list of (label, value, help_text) or (label, value, help_text, delta)."""
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        label, value, help_text = item[0], item[1], item[2]
        delta = item[3] if len(item) > 3 else None
        col.metric(label, value, delta=delta, help=help_text)


def render_footer():
    st.divider()
    with st.expander("Data sources, method and limits"):
        st.markdown(
            """
**Sources.** District indicators come from the NISR EICV7 Education Thematic Report (2023/24), Annex tables A.3, A.5 and A.11.
Climate hazard and school feeding coverage are district profiles aligned with MINEMA and Meteo Rwanda categories.

**Student records are simulated.** No real student data is used. An operational deployment would connect to authorised systems such as SDMS and CAMIS.

**District figures are averages.** They describe areas, not individual children, and a high district value points to a systemic challenge, not individual fault.

**The risk model is a transparent logistic score.** Its coefficients are fixed, documented values for this prototype. A warning is a prompt for a teacher to follow up, not a prediction that a child will drop out.
"""
        )