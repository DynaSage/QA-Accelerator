from typing import Any

__all__ = ["build_qa_sql_agent"]


def __getattr__(name: str) -> Any:
    if name == "build_qa_sql_agent":
        from src.graph.sql_agent_graph import build_qa_sql_agent

        return build_qa_sql_agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
