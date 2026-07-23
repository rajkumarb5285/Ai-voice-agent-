"""
Wellness Agent Node
Tracks habits, provides fitness/mental health support, and coaching.
"""
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import logger

WELLNESS_SYSTEM_PROMPT = """You are a compassionate wellness coach and life mentor.

Your approach:
- Listen with empathy and without judgment
- Provide evidence-based health and wellness advice
- Help with stress management and mental clarity
- Support habit formation using behavioral science (habit loops, streaks)
- Encourage sustainable fitness and nutrition habits
- Celebrate small wins and progress
- Know when to suggest professional help (therapy, doctors)

IMPORTANT: You are supportive but NOT a replacement for medical or mental health professionals.
Always recommend professional help for serious concerns.

User's wellness context:
{user_context}
"""

llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.6,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)


async def wellness_agent_node(state: AgentState) -> AgentState:
    if "wellness_agent" not in state.get("selected_agents", []):
        return state

    start = time.time()
    user_input = state["user_input"]
    user_ctx = state.get("long_term_context", "")

    logger.info("wellness_agent_start")

    try:
        response = await llm.ainvoke([
            SystemMessage(content=WELLNESS_SYSTEM_PROMPT.format(user_context=user_ctx[:400])),
            HumanMessage(content=user_input),
        ])
        wellness_output = response.content

        # Store emotional state in episodic memory
        memories = []
        emotional_keywords = ["stressed", "anxious", "happy", "sad", "overwhelmed", "tired", "energetic"]
        if any(kw in user_input.lower() for kw in emotional_keywords):
            memories.append({
                "content": f"User expressed: {user_input[:100]}",
                "category": "wellness",
                "title": "Emotional Check-in",
                "importance_score": 0.5,
            })

    except Exception as e:
        wellness_output = f"Wellness coach error: {str(e)}"
        memories = []
        logger.error("wellness_agent_error", error=str(e))

    latency = int((time.time() - start) * 1000)
    activity = {
        "agent_name": "Wellness Coach",
        "action": "Provided wellness support",
        "status": "completed",
        "output_summary": wellness_output[:150],
        "duration_ms": latency,
    }

    current_outputs = state.get("agent_outputs", {})
    current_outputs["wellness_agent"] = wellness_output

    return {
        **state,
        "agent_outputs": current_outputs,
        "memories_to_store": state.get("memories_to_store", []) + memories,
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }
