import html as html_module

import streamlit as st

_CSS = """
<style>
details.story-card-wrap {
  background: var(--md-surface-container,#1a2330);
  border: 1px solid var(--outline-variant,#26333f);
  border-radius: var(--shape-xl,24px);
  margin-bottom: 16px; overflow: hidden;
  transition: border-color 0.15s, box-shadow 0.15s;
}
details.story-card-wrap:hover {
  border-color: var(--outline,#3a4758);
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
details.story-card-wrap summary {
  display: flex; align-items: center; gap: 12px;
  padding: 13px 16px; cursor: pointer; list-style: none;
  transition: background 0.15s;
}
details.story-card-wrap summary::-webkit-details-marker { display: none; }
details.story-card-wrap summary:hover {
  background: var(--md-surface-container-high,#202c3c);
}
.story-id-chip {
  font-size: 11px; font-weight: 700; padding: 3px 9px;
  border-radius: 999px; background: var(--primary-container,#0c4369);
  color: var(--primary,#38bdf8); white-space: nowrap; flex-shrink: 0;
}
.story-title {
  font-size: 13px; font-weight: 600;
  color: var(--text,#dde4ee); flex: 1;
}
.story-badge {
  font-size: 11px; font-weight: 600; padding: 3px 10px;
  border-radius: 999px; border: 1px solid var(--outline-variant,#26333f);
  color: var(--muted,#92a1b5); white-space: nowrap; flex-shrink: 0;
}
.story-chevron {
  width: 18px; height: 18px; flex-shrink: 0; color: var(--muted,#92a1b5);
  transition: transform 0.25s cubic-bezier(0.34,1.56,0.64,1);
}
details.story-card-wrap[open] .story-chevron { transform: rotate(180deg); }
.story-body {
  padding: 16px 18px; border-top: 1px solid var(--outline-variant,#26333f);
  background: var(--md-surface-container-low,#141c26);
}
.story-section-label {
  font-size: 11px; font-weight: 700; text-transform: uppercase;
  letter-spacing: 0.08em; color: var(--primary,#38bdf8);
  margin: 12px 0 5px;
}
.story-section-label:first-child { margin-top: 0; }
.story-section-text {
  font-size: 13px; color: var(--text,#dde4ee); line-height: 1.6;
  white-space: pre-wrap;
}
</style>
"""

_CHEVRON = (
    '<svg class="story-chevron" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
    'fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="6 9 12 15 18 9"/></svg>'
)


def render_story_card(story: dict) -> None:
    story_id   = story.get("id", "N/A")
    title      = html_module.escape(story.get("title") or "Untitled")
    work_type  = html_module.escape(story.get("work_item_type") or "Story")
    state_val  = html_module.escape(story.get("state") or "")
    tags       = html_module.escape(story.get("tags") or "")
    desc       = html_module.escape(story.get("description") or "No description provided.")
    acceptance = html_module.escape(story.get("acceptance_criteria") or "No acceptance criteria provided.")

    tag_html = f'<span class="story-badge">{tags}</span>' if tags else ""
    state_html = f'<span class="story-badge">{state_val}</span>' if state_val else ""

    html_out = (
        _CSS
        + f'<details class="story-card-wrap">'
        + f'<summary>'
        + f'<span class="story-id-chip">US-{story_id}</span>'
        + f'<span class="story-title">{title}</span>'
        + f'<span class="story-badge">{work_type}</span>'
        + state_html
        + tag_html
        + _CHEVRON
        + '</summary>'
        + '<div class="story-body">'
        + '<div class="story-section-label">Description</div>'
        + f'<div class="story-section-text">{desc}</div>'
        + '<div class="story-section-label">Acceptance Criteria</div>'
        + f'<div class="story-section-text">{acceptance}</div>'
        + '</div></details>'
    )
    st.markdown(html_out, unsafe_allow_html=True)
