from langgraph.graph import END, START, StateGraph

from aiproject.nodes import answer_node, retrieve_node
from aiproject.state import AgentState


def build_graph():
    workflow = StateGraph(AgentState)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("answer", answer_node)
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "answer")
    workflow.add_edge("answer", END)
    return workflow.compile()


graph = build_graph()
