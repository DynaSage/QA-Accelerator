import streamlit as st

WORKFLOW_STEPS = ["Import", "Build", "Review", "Generate", "Export"]

_STEP_LABELS = {
    "Import":   "Import",
    "Build":    "Build Spec",
    "Review":   "Review",
    "Generate": "Generate",
    "Export":   "Export",
}

_CHECK_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'width="12" height="12" fill="none" stroke="currentColor" '
    'stroke-width="3" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="20 6 9 17 4 12"/></svg>'
)


_CSS = """
<style>
@keyframes pulse-ring {
  0%   { box-shadow: 0 0 0 0px  rgba(56,189,248,0.4); }
  70%  { box-shadow: 0 0 0 8px  rgba(56,189,248,0.0); }
  100% { box-shadow: 0 0 0 0px  rgba(56,189,248,0.0); }
}
@keyframes step-fade-in {
  from { opacity:0; transform:translateY(4px) scale(0.97); }
  to   { opacity:1; transform:none; }
}
.m3-stepper-track {
  display:flex; align-items:center; margin-bottom:1.5rem;
  background:var(--md-surface-container-low,#141c26);
  border:1px solid var(--outline-variant,#26333f);
  border-radius:var(--shape-2xl,28px);
  padding:14px 22px; overflow-x:auto; gap:0;
  animation:step-fade-in 0.35s cubic-bezier(0.22,1,0.36,1) both;
}
.m3-step-item  { display:flex; align-items:center; flex-shrink:0; }
.m3-step-node  { display:flex; align-items:center; gap:8px; white-space:nowrap; }
.m3-step-connector {
  display:inline-block; width:32px; height:2px;
  background:var(--outline-variant,#26333f);
  border-radius:1px; margin:0 10px; flex-shrink:0;
}
.m3-step-dot {
  width:24px; height:24px; border-radius:50%;
  display:inline-flex; align-items:center; justify-content:center;
  font-size:11px; font-weight:700; flex-shrink:0;
  transition:all 0.25s cubic-bezier(0.34,1.56,0.64,1);
}
.m3-step-dot.done {
  background:var(--secondary-container,#143d22);
  color:var(--secondary,#4ade80);
  border:1.5px solid var(--secondary,#4ade80);
}
.m3-step-dot.active {
  background:var(--primary-container,#0c4369);
  color:var(--primary,#38bdf8);
  border:2px solid var(--primary,#38bdf8);
  animation:pulse-ring 2s ease-out infinite;
}
.m3-step-dot.pending {
  background:var(--md-surface-container-high,#202c3c);
  color:var(--muted,#92a1b5);
  border:1.5px solid var(--outline-variant,#26333f);
}
.m3-step-label { font-size:12px; font-weight:600; }
.m3-step-label.done    { color:var(--secondary,#4ade80); }
.m3-step-label.active  { color:var(--on-primary-container,#d0eeff); font-weight:700; }
.m3-step-label.pending { color:var(--muted,#92a1b5); }
</style>
"""


def render_stepper(current_step: str) -> None:
    try:
        current_index = WORKFLOW_STEPS.index(current_step)
    except ValueError:
        current_index = 0

    items_html = ""
    for idx, step in enumerate(WORKFLOW_STEPS):
        label = _STEP_LABELS.get(step, step)
        if idx < current_index:
            state = "done"
            dot_content = _CHECK_SVG
        elif idx == current_index:
            state = "active"
            dot_content = str(idx + 1)
        else:
            state = "pending"
            dot_content = str(idx + 1)
        sep = '<span class="m3-step-connector"></span>' if idx < len(WORKFLOW_STEPS) - 1 else ""
        items_html += (
            f'<div class="m3-step-item">'
            f'<div class="m3-step-node {state}">'
            f'<span class="m3-step-dot {state}">{dot_content}</span>'
            f'<span class="m3-step-label {state}">{label}</span>'
            f"</div>{sep}</div>"
        )

    st.markdown(
        _CSS + f'<div class="m3-stepper-track">{items_html}</div>',
        unsafe_allow_html=True,
    )
