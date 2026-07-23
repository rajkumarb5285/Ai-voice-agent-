"""
Learning Coach Agent
Creates personalized learning plans, explains concepts, tracks progress.
"""
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import logger

LEARNING_SYSTEM_PROMPT = """You are an expert learning coach and mentor.

Your approach:
- Adapt explanations to the learner's current level
- Use the Feynman technique: explain simply first, then add depth
- Create structured learning paths with milestones
- Recommend high-quality resources (books, courses, practice projects)
- Use analogies and real-world examples
- Break down complex topics into digestible chunks
- Celebrate progress and maintain motivation

Learner Profile:
{user_context}

Recent Learning History:
{episodic_context}
"""

llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.5,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)


async def learning_agent_node(state: AgentState) -> AgentState:
    if "learning_agent" not in state.get("selected_agents", []):
        return state

    start = time.time()
    user_input = state["user_input"]
    user_ctx = state.get("long_term_context", "")
    episodic_ctx = state.get("episodic_context", "")

    logger.info("learning_agent_start", request=user_input[:100])

    try:
        response = await llm.ainvoke([
            SystemMessage(content=LEARNING_SYSTEM_PROMPT.format(
                user_context=user_ctx[:400],
                episodic_context=episodic_ctx[:300],
            )),
            HumanMessage(content=user_input),
        ])
        learning_output = response.content
    except Exception as e:
        learning_output = f"Learning coach error: {str(e)}"
        logger.error("learning_agent_error", error=str(e))

    latency = int((time.time() - start) * 1000)
    activity = {
        "agent_name": "Learning Coach",
        "action": "Created personalized learning guidance",
        "status": "completed",
        "output_summary": learning_output[:150],
        "duration_ms": latency,
    }

    current_outputs = state.get("agent_outputs", {})
    current_outputs["learning_agent"] = learning_output

    return {
        **state,
        "agent_outputs": current_outputs,
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }
