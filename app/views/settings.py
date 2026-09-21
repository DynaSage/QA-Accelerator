import streamlit as st

from app.components.theme import page_header
from src.config import get_connection_status


def render() -> None:
    page_header("Settings & Health", "Check service connectivity and environment configuration.")

    st.subheader("Connection Status")
    statuses = get_connection_status()
    for key, item in statuses.items():
        icon = "✅" if item["status"] == "ready" else "⚠️"
        st.markdown(f"**{item['label']}** — {icon} {item['status'].title()}")
        st.caption(item["detail"])

    st.divider()
    st.subheader("Connection Tests")

    if st.button("Test Azure OpenAI"):
        try:
            from langchain_core.messages import HumanMessage

            from src.config import get_azure_llm

            response = get_azure_llm().invoke([HumanMessage(content="Reply with OK only.")])
            st.success(f"Azure OpenAI responded: {str(response.content)[:120]}")
        except Exception as exc:
            st.error(str(exc))

    if st.button("Test Azure DevOps"):
        try:
            from src.integrations.azure_devops_client import AzureDevOpsClient

            result = AzureDevOpsClient().test_connection()
            st.success(f"Connected to {result['organization']}/{result['project']}")
        except Exception as exc:
            st.error(str(exc))

    if st.button("Test Databricks Config"):
        from src.config import get_databricks_settings

        settings = get_databricks_settings()
        if settings.is_dummy:
            st.warning("Databricks credentials are not configured.")
        else:
            st.success(f"Databricks config present for {settings.server_hostname}")

    st.divider()
    st.subheader("Environment Notes")
    st.markdown(
        """
        - Credentials are loaded from `.env` in the project root.
        - Secrets are never displayed in the UI.
        - Update `.env` and refresh this page after changing credentials.
        """
    )
