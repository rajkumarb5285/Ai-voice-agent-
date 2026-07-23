"""
Career Coach Agent Node
Resume review, interview prep, skill gap analysis, career planning.
"""
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import logger

CAREER_SYSTEM_PROMPT = """You are an elite career coach with expertise in tech and professional development.

Your capabilities:
- Conduct detailed skill gap analysis
- Create personalized career roadmaps
- Prepare candidates for technical and behavioral interviews
- Review and improve resumes/CVs
- Advise on salary negotiation
- Identify high-value skills and certifications to pursue
- Provide insights on job market trends

Interview prep includes:
- STAR method for behavioral questions
- Technical problem-solving frameworks
- Role-specific preparation
- Common question patterns

Career context for this user:
{user_context}

Learning history:
{episodic_context}
"""

llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.4,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)


async def career_agent_node(state: AgentState) -> AgentState:
    if "career_agent" not in state.get("selected_agents", []):
        return state

    start = time.time()
    user_input = state["user_input"]
    user_ctx = state.get("long_term_context", "")
    episodic_ctx = state.get("episodic_context", "")

    logger.info("career_agent_start", request=user_input[:100])

    try:
        response = await llm.ainvoke([
            SystemMessage(content=CAREER_SYSTEM_PROMPT.format(
                user_context=user_ctx[:400],
                episodic_context=episodic_ctx[:300],
            )),
            HumanMessage(content=user_input),
        ])
        career_output = response.content

        # Store career milestones
        memories = []
        if any(kw in user_input.lower() for kw in ["interview", "job offer", "promotion", "new role", "career goal"]):
            memories.append({
                "content": f"Career milestone/event: {user_input[:100]}",
                "category": "career",
                "title": "Career Event",
                "importance_score": 0.8,
            })

    except Exception as e:
        career_output = f"Career coach error: {str(e)}"
        memories = []
        logger.error("career_agent_error", error=str(e))

    latency = int((time.time() - start) * 1000)
    activity = {
        "agent_name": "Career Coach",
        "action": "Provided career guidance",
        "status": "completed",
        "output_summary": career_output[:150],
        "duration_ms": latency,
    }

    current_outputs = state.get("agent_outputs", {})
    current_outputs["career_agent"] = career_output

    return {
        **state,
        "agent_outputs": current_outputs,
        "memories_to_store": state.get("memories_to_store", []) + memories,
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }
