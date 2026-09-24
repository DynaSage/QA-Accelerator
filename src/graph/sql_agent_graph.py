from langgraph.graph import END, START, StateGraph

from src.agents.reporting_agent import format_qa_report
from src.agents.test_case_agent import generate_test_cases
from src.graph.nodes import analyze_spec, execute_on_adb, generate_sql_tests, safety_check
from src.graph.state import AgentState


def build_qa_sql_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("analyze_spec", analyze_spec)
    workflow.add_node("generate_sql_tests", generate_sql_tests)
    workflow.add_node("generate_test_cases", generate_test_cases)
    workflow.add_node("safety_check", safety_check)
    workflow.add_node("execute_on_adb", execute_on_adb)
    workflow.add_node("format_qa_report", format_qa_report)

    workflow.add_edge(START, "analyze_spec")
    workflow.add_edge("analyze_spec", "generate_sql_tests")
    workflow.add_edge("generate_sql_tests", "safety_check")
    workflow.add_edge("safety_check", "generate_test_cases")
    workflow.add_edge("generate_test_cases", "execute_on_adb")
    workflow.add_edge("execute_on_adb", "format_qa_report")
    workflow.add_edge("format_qa_report", END)
    return workflow.compile()
