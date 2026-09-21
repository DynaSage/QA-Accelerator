import html as html_module

import streamlit as st

from src.config import get_connection_status


_STATUS_ACCENT = {
    "ready":     ("var(--secondary,#4ade80)",   "var(--secondary-container,#143d22)", "var(--card-pass-border,#166534)"),
    "attention": ("var(--warning,#fbbf24)",     "var(--warning-container,#3d2a07)",   "var(--card-warn-border,#854d0e)"),
    "error":     ("var(--error,#f87171)",       "var(--error-container,#5c1818)",     "var(--card-fail-border,#991b1b)"),
}

_CSS = """
<style>
.conn-grid {
  display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 1.25rem;
}
.conn-card {
  flex: 1; min-width: 160px;
  background: var(--md-surface-container,#1a2330);
  border: 1px solid var(--outline-variant,#26333f);
  border-radius: var(--shape-2xl,28px);
  padding: 18px 20px; position: relative; overflow: hidden;
  transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1),
              box-shadow 0.25s cubic-bezier(0.2,0,0,1);
}
.conn-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 32px rgba(0,0,0,0.4);
}
.conn-card .conn-label {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.09em; color: var(--muted,#92a1b5); margin-bottom: 10px;
}
.conn-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 12px; border-radius: var(--shape-full,999px);
  font-size: 12px; font-weight: 700; margin-bottom: 8px;
  border: 1px solid;
}
.conn-badge::before {
  content: ""; width: 7px; height: 7px; border-radius: 50%;
  background: currentColor;
}
.conn-detail {
  font-size: 12px; color: var(--muted,#92a1b5); font-family: monospace;
  word-break: break-all;
}
</style>
"""


def render_connection_cards() -> None:
    statuses = get_connection_status()
    cards_html = ""
    for key, item in statuses.items():
        is_ready = item["status"] == "ready"
        state = "ready" if is_ready else ("error" if item["status"] == "error" else "attention")
        accent, bg, border = _STATUS_ACCENT.get(state, _STATUS_ACCENT["attention"])
        status_label = "Ready" if is_ready else item["status"].title()
        label  = html_module.escape(item["label"])
        detail = html_module.escape(item["detail"])
        cards_html += (
            f'<div class="conn-card" style="border-left:3px solid {accent};">'
            f'<div class="conn-label">{label}</div>'
            f'<div class="conn-badge" style="color:{accent};background:{bg};border-color:{border}50;">'
            f'{status_label}</div>'
            f'<div class="conn-detail">{detail}</div></div>'
        )
    st.markdown(
        _CSS + f'<div class="conn-grid">{cards_html}</div>',
        unsafe_allow_html=True,
    )
