"""
Intent Classifier Node
Analyzes user input → determines intent, entities, and which agents to activate.

Voice Pipeline Step: User Input → [Intent Classifier] → Agent Selection
"""
import json
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import logger

INTENT_SYSTEM_PROMPT = """You are an intent classifier for a personal AI assistant.
Analyze the user's message and return a JSON object with:
{
  "intent": "<primary intent>",
  "confidence": <0.0-1.0>,
  "sub_intents": ["<sub1>", "<sub2>"],
  "entities": {"<key>": "<value>"},
  "selected_agents": ["<agent1>", "<agent2>"],
  "response_mode": "conversational|structured|brief"
}

Intent categories:
- general_chat: casual conversation, greetings, emotions
- research: web search, facts, news, information gathering
- coding: write code, debug, explain code, review code
- planning: break down tasks, create plans, set goals
- productivity: calendar, tasks, reminders, scheduling
- learning: explain concepts, study plans, resources, tutoring
- wellness: habits, fitness, stress, motivation, mental health
- career: resume, interview prep, job search, skill gaps
- email: read/write/summarize emails
- analysis: analyze data, files, charts
- memory: remember this, what did I say, recall

Agent mapping:
- general_chat → ["orchestrator"]
- research → ["research_agent"]
- coding → ["coding_agent"]
- planning → ["planner_agent"]
- productivity → ["productivity_agent"]
- learning → ["learning_agent"]
- wellness → ["wellness_agent"]
- career → ["career_agent"]
- email → ["email_agent"]
- analysis → ["research_agent", "coding_agent"]
- memory → ["memory_agent"]

Always select the most specific agents. For complex requests, select multiple agents.
"""

_ic_base_url = settings.openai_base_url or ""
_classifier_model = "gpt-4o-mini" if not ("ollama" in settings.openai_api_key or "11434" in _ic_base_url) else settings.llm_model
llm = ChatOpenAI(
    model=_classifier_model,
    temperature=0.0,  # Zero temp for deterministic classification
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
    max_tokens=256,   # Classification only needs a tiny JSON output
)


def classify_intent_by_keywords(text: str) -> dict:
    text = text.lower()
    matched_intents = []
    
    if any(k in text for k in ["search", "google", "weather", "news", "find", "research", "browse"]):
        matched_intents.append(("research", "research_agent"))
    if any(k in text for k in ["code", "python", "javascript", "program", "function", "bug", "compile", "script", "developer", "html", "css"]):
        matched_intents.append(("coding", "coding_agent"))
    if any(k in text for k in ["plan", "goal", "breakdown", "todo", "steps", "tasks", "milestones"]):
        matched_intents.append(("planning", "planner_agent"))
    if any(k in text for k in ["task", "reminder", "calendar", "schedule", "event", "meeting", "todo", "agenda"]):
        matched_intents.append(("productivity", "productivity_agent"))
    if any(k in text for k in ["learn", "study", "explain", "understand", "concept", "course", "tutor"]):
        matched_intents.append(("learning", "learning_agent"))
    if any(k in text for k in ["wellness", "fitness", "health", "diet", "sleep", "stress", "meditate", "breathing"]):
        matched_intents.append(("wellness", "wellness_agent"))
    if any(k in text for k in ["career", "job", "resume", "interview", "hire", "salary"]):
        matched_intents.append(("career", "career_agent"))
    if any(k in text for k in ["email", "mail", "inbox", "gmail", "draft"]):
        matched_intents.append(("email", "email_agent"))
    if any(k in text for k in ["remember", "forget", "recall", "memory", "store", "fact"]):
        matched_intents.append(("memory", "memory_agent"))

    # If one or more intents are matched, use the first one as a fast path.
    if len(matched_intents) >= 1:
        intent, agent = matched_intents[0]
        return {
            "intent": intent,
            "confidence": 0.9,
            "sub_intents": [m[0] for m in matched_intents[1:]],
            "entities": {},
            "selected_agents": [agent],
            "response_mode": "conversational",
        }

    return {
        "intent": "general_chat",
        "confidence": 0.9,
        "sub_intents": [],
        "entities": {},
        "selected_agents": ["orchestrator"],
        "response_mode": "conversational",
    }


def is_casual_conversation(text: str) -> bool:
    import re
    clean = re.sub(r'[^\w\s]', '', text.lower()).strip()
    
    greetings = {
        "hi", "hello", "hey", "hola", "namaste", "good morning", "good afternoon", "good evening", 
        "how are you", "who are you", "whats up", "hows it going", "greetings", "yo",
        "tell me about yourself", "who is ava", "introduce yourself", "are you ava", "your name",
        "ava", "whats your name", "what is your name", "who are you"
    }
    
    if clean in greetings or any(clean.startswith(g) for g in greetings):
        return True
        
    specialist_keywords = [
        "search", "google", "weather", "news", "find", "research", "browse",
        "code", "python", "javascript", "program", "function", "bug", "compile", "script",
        "plan", "goal", "breakdown", "todo", "steps", "tasks", "milestones",
        "task", "reminder", "calendar", "schedule", "event", "meeting", "todo", "agenda",
        "learn", "study", "explain", "understand", "concept", "course",
        "wellness", "fitness", "health", "diet", "sleep", "stress", "meditate", "breathing",
        "career", "job", "resume", "interview", "hire", "salary",
        "email", "mail", "inbox", "gmail", "draft",
        "remember", "forget", "recall", "memory", "store"
    ]
    
    words = clean.split()
    if len(words) <= 3 and not any(kw in clean for kw in specialist_keywords):
        return True
        
    return False


async def intent_classifier_node(state: AgentState) -> AgentState:
    """Classify user intent and determine which agents to activate.

    Fast path: keyword matching covers ~90% of queries with no LLM call.
    Slow path: LLM is only invoked when the keyword classifier is uncertain
               (i.e. defaults to general_chat with no strong signal).
    """
    start = time.time()
    user_input = state["user_input"]

    logger.info("intent_classifier_start", input_preview=user_input[:100])

    # --- Fast path: keyword classification (zero latency) ---
    keyword_result = classify_intent_by_keywords(user_input)
    use_llm = keyword_result["intent"] == "general_chat"
    if use_llm and (is_casual_conversation(user_input) or state.get("input_mode") == "voice"):
        use_llm = False
    if use_llm and (settings.fast_intent_classification or "ollama" in settings.openai_api_key or "11434" in (settings.openai_base_url or "")):
        use_llm = False


    result = None
    if use_llm:
        # Only hit the LLM when we have no clear keyword signal
        try:
            response = await llm.ainvoke([
                SystemMessage(content=INTENT_SYSTEM_PROMPT),
                HumanMessage(content=f"Classify this message: {user_input}"),
            ])

            content = response.content.strip()
            import re
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except Exception:
                    pass

            if not result:
                try:
                    result = json.loads(content)
                except Exception:
                    pass
        except Exception as e:
            logger.error("intent_classifier_llm_error", error=str(e))

    # Fall back to keyword result if LLM failed or was skipped
    if not result or not isinstance(result, dict) or "intent" not in result:
        if use_llm:
            logger.info("intent_classifier_using_keyword_fallback")
        else:
            logger.info("intent_classifier_keyword_fast_path", intent=keyword_result["intent"])
        result = keyword_result

    latency = int((time.time() - start) * 1000)
    logger.info(
        "intent_classified",
        intent=result.get("intent"),
        confidence=result.get("confidence"),
        agents=result.get("selected_agents"),
        latency_ms=latency,
        used_llm=use_llm,
    )

    activity = {
        "agent_name": "Intent Classifier",
        "action": f"Classified intent as '{result.get('intent')}'",
        "status": "completed",
        "duration_ms": latency,
    }

    return {
        **state,
        "intent": result.get("intent", "general_chat"),
        "intent_confidence": result.get("confidence", 0.8),
        "sub_intents": result.get("sub_intents", []),
        "entities": result.get("entities", {}),
        "selected_agents": result.get("selected_agents", ["orchestrator"]),
        "response_mode": result.get("response_mode", "conversational"),
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }
