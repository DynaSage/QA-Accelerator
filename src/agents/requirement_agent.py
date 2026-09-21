import json

from src.config import adb_runtime_context
from src.prompts.requirement_prompts import REQUIREMENT_AGENT_PROMPT, REQUIREMENT_AGENT_SYSTEM_PROMPT
from src.utils.llm_json import invoke_llm_json


def analyze_requirements(requirement_text: str) -> dict:
    if not requirement_text.strip():
        return {
            "source_table": "",
            "target_table": "",
            "primary_key": "",
            "load_type": "",
            "incremental_column": "",
            "watermark_column": "",
            "transformation_rules": [],
            "business_rules": [],
            "not_null_columns": [],
            "missing_information": [],
            "assumptions": [
                "No user story or requirement document was supplied. The mapping document is the source of truth."
            ],
            "requirement_summary": "Mapping document only; no Azure DevOps stories or requirement document.",
        }

    payload = invoke_llm_json(
        REQUIREMENT_AGENT_PROMPT.format(requirement_text=requirement_text),
        system_prompt=REQUIREMENT_AGENT_SYSTEM_PROMPT,
    )
    payload.setdefault("missing_information", [])
    payload.setdefault("assumptions", [])
    payload.setdefault("transformation_rules", [])
    payload.setdefault("business_rules", [])
    payload.setdefault("not_null_columns", [])
    payload["adb_context"] = adb_runtime_context()
    return payload
