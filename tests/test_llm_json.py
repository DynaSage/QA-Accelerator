import json

import pytest

from src.utils.llm_json import extract_llm_text, parse_llm_json


def test_extract_llm_text_from_string():
    assert extract_llm_text('{"ok": true}') == '{"ok": true}'


def test_extract_llm_text_from_response_blocks():
    content = [{"type": "text", "text": '{"missing_information": []}'}]
    assert extract_llm_text(content) == '{"missing_information": []}'


def test_parse_llm_json_from_markdown_fence():
    payload = parse_llm_json('```json\n{"assumptions": ["a"]}\n```')
    assert payload["assumptions"] == ["a"]


def test_parse_llm_json_embedded_object():
    payload = parse_llm_json('Here is the result: {"validation_plan": ["Record Count"]} end')
    assert payload["validation_plan"] == ["Record Count"]


def test_parse_llm_json_rejects_non_object():
    with pytest.raises(ValueError):
        parse_llm_json(json.dumps(["not", "an", "object"]))
