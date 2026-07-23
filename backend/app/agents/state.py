"""
LangGraph Agent State
Defines the shared state that flows through all nodes in the graph.
"""
from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    # Core conversation
    messages: Annotated[List[BaseMessage], operator.add]
    user_id: str
    conversation_id: str
    session_id: str

    # Current input
    user_input: str
    input_mode: str  # "text" | "voice"
    language: Optional[str]  # e.g., "hi-IN"

    # Intent classification
    intent: str
    # e.g. "general_chat" | "research" | "coding" | "planning" |
    #       "productivity" | "learning" | "wellness" | "career" | "email"
    intent_confidence: float
    entities: Dict[str, Any]
    sub_intents: List[str]

    # Memory context (injected before agent processing)
    short_term_context: str
    long_term_context: str
    semantic_context: str
    episodic_context: str

    # Which specialist agents to invoke
    selected_agents: List[str]

    # Agent outputs (merged)
    agent_outputs: Dict[str, str]

    # Tool call results
    tool_results: Dict[str, Any]

    # Planning
    plan: Optional[List[Dict[str, Any]]]

    # Final response
    final_response: str
    response_mode: str  # "conversational" | "structured" | "brief"

    # Agent activity log (streamed to frontend)
    agent_activities: List[Dict[str, Any]]

    # Memories to store after this turn
    memories_to_store: List[Dict[str, Any]]

    # Error handling
    error: Optional[str]
    retry_count: int

    # Metadata
    total_tokens: int
    total_latency_ms: int
