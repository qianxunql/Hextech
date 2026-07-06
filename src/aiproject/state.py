from langgraph.graph import MessagesState


class AgentState(MessagesState):
    """Shared state passed between LangGraph nodes."""

    context: list[str]
    sources: list[str]
