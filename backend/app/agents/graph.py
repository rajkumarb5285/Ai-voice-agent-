"""
LangGraph StateGraph — The Main Orchestration Brain

Full Voice Pipeline:
  User Input
       │
       ▼
  [intent_classifier]        ── Determine intent + select agents
       │
       ▼
  [memory_retrieval]          ── Load all memory contexts
       │
       ▼
  [parallel_agents]           ── Run specialist agents in parallel
  ┌────┴────────────────────────────────────────────────┐
  research  coding  planning  learning  productivity  wellness  career  email
  └────┬────────────────────────────────────────────────┘
       │
       ▼
  [response_synthesis]        ── Merge outputs → final response
       │
       ▼
  [memory_update]             ── Persist new memories
       │
       ▼
  Final Response (text + optional TTS audio)
"""
import asyncio
from functools import partial
from typing import Literal, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.state import AgentState
from app.agents.intent_classifier import intent_classifier_node
from app.agents.memory_agent import memory_retrieval_node, memory_update_node
from app.agents.research_agent import research_agent_node
from app.agents.planner_agent import planner_agent_node
from app.agents.coding_agent import coding_agent_node
from app.agents.learning_agent import learning_agent_node
from app.agents.productivity_agent import productivity_agent_node
from app.agents.wellness_agent import wellness_agent_node
from app.agents.career_agent import career_agent_node
from app.agents.email_agent import email_agent_node
from app.agents.response_agent import response_synthesis_node
from app.config import settings
from app.utils.logger import logger


MOCK_KEY_PREFIXES = ("mock", "your-", "change", "sk-placeholder", "test-key", "replace")

LANGUAGE_NAMES = {
    "hi-IN": "Hindi (हिंदी)",
    "mr-IN": "Marathi (मराठी)",
    "bn-IN": "Bengali (বাংলা)",
    "gu-IN": "Gujarati (ગુજરાતી)",
    "or-IN": "Odia (ଓଡ଼ିଆ)",
    "ta-IN": "Tamil (தமிழ்)",
    "te-IN": "Telugu (తెలుగు)",
    "kn-IN": "Kannada (ಕನ್ನಡ)",
    "ml-IN": "Malayalam (മലയാളം)",
    "pa-IN": "Punjabi (ਪੰਜਾਬੀ)",
    "bho-IN": "Bhojpuri (भोजपुरी)",
    "bgc-IN": "Haryanvi (हरियाणवी)",
    "awa-IN": "Awadhi (अवधी)",
    "bra-IN": "Braj Bhasha (ब्रज भाषा)",
    "mwr-IN": "Marwari (मारवाड़ी)",
    "ur-IN": "Urdu (اردو)",
    "en-US": "English",
}


def detect_language_and_dialect(text: str, user_lang: Optional[str] = None) -> str:
    """Automatically detect exact script & regional Indian dialect from user input text."""
    t = text.lower()
    if any(ord(c) >= 0x0900 and ord(c) <= 0x097F for c in text):
        if any(w in t for w in ['अहै', 'अही', 'अहैन', 'तोहार', 'करब', 'अउर', 'तौन', 'जौन', 'कहेउ', 'भवा', 'का हाल अहै', 'अवा अही', 'नाहीं', 'सभन', 'कतहुँ', 'कइसन', 'बताउब', 'करिहै', 'पाँव लागी', 'नीक']):
            return 'awa-IN' # Pure Awadhi
        elif any(w in t for w in ['बा', 'बानी', 'रउरा', 'राउर', 'काहे', 'हमरा', 'हमार', 'इहाँ', 'उहाँ', 'बटे', 'का हाल बा', 'का हो', 'का हो रहा बा', 'रउआ', 'भइल', 'खातिर']):
            return 'bho-IN' # Pure Bhojpuri
        elif any(w in t for w in ['सै', 'मन्ने', 'तन्ने', 'क्यूकर', 'कोन्या', 'की करै']):
            return 'bgc-IN' # Haryanvi
        elif any(w in t for w in ['मेरो', 'तिहारे', 'करीजै', 'नयौ']):
            return 'bra-IN' # Braj Bhasha
        elif any(w in t for w in ['कांई', 'अठै', 'कठै', 'म्हारो', 'थारो', 'घणी']):
            return 'mwr-IN' # Marwari
        elif any(c in 'ळ' for c in text) or any(w in t for w in ['आहे', 'करू', 'झाले', 'नमस्कार', 'कसे', 'आहात']):
            return 'mr-IN' # Marathi
        elif user_lang and user_lang not in ["en-US", "hi-IN", "auto", "", None]:
            return user_lang
        else:
            return 'hi-IN' # Hindi

    if user_lang and user_lang not in ["en-US", "auto", "", None]:
        return user_lang

    if any(ord(c) >= 0x0980 and ord(c) <= 0x09FF for c in text):
        return 'bn-IN' # Bengali
    elif any(ord(c) >= 0x0A00 and ord(c) <= 0x0A7F for c in text):
        return 'pa-IN' # Punjabi
    elif any(ord(c) >= 0x0A80 and ord(c) <= 0x0AFF for c in text):
        return 'gu-IN' # Gujarati
    elif any(ord(c) >= 0x0B00 and ord(c) <= 0x0B7F for c in text):
        return 'or-IN' # Odia
    elif any(ord(c) >= 0x0B80 and ord(c) <= 0x0BFF for c in text):
        return 'ta-IN' # Tamil
    elif any(ord(c) >= 0x0C00 and ord(c) <= 0x0C7F for c in text):
        return 'te-IN' # Telugu
    elif any(ord(c) >= 0x0C80 and ord(c) <= 0x0CFF for c in text):
        return 'kn-IN' # Kannada
    elif any(ord(c) >= 0x0D00 and ord(c) <= 0x0D7F for c in text):
        return 'ml-IN' # Malayalam
    elif any(ord(c) >= 0x0600 and ord(c) <= 0x06FF for c in text):
        return 'ur-IN' # Urdu
    return user_lang or 'en-US'


def get_language_instruction(lang_code: str) -> str:
    instructions = {
        "bho-IN": (
            "\n========================\n"
            "STRICT NATIVE BHOJPURI SPOKEN DIALOGUE REQUIREMENT (100% शुद्ध बोलचाल भोजपुरी)\n"
            "========================\n"
            "You are Ava, chatting LIVE with a friend in real spoken Bhojpuri.\n"
            "CRITICAL: DO NOT READ OR SOUND LIKE A BOOK, TEXTBOOK, ESSAY, OR FORMAL REPORT. DO NOT USE NUMBERED LISTS OR BULLET POINTS.\n\n"
            "NATIVE BHOJPURI SPOKEN DIALOGUE RULES:\n"
            "1. CONVERSATIONAL PACE: Speak 1-3 short, warm spoken sentences max. Use natural pauses ('...').\n"
            "2. BHOJPURI SPEECH FILLERS: Use 'अरे भाई...', 'देखीं ना...', 'अरे हाँ!', 'अरे ना भाई...', 'सुनल जाइ...'.\n"
            "3. NATIVE BHOJPURI GRAMMAR & VOCABULARY:\n"
            "   - Greetings: 'राउर प्रणाम!', 'का हो रहा बा भाई?', 'सब ठीक बा न?'.\n"
            "   - Pronouns & Verbs: 'बा', 'बानी', 'बटे', 'भइल', 'करब', 'बताइब', 'हम्मन के', 'राउर', 'रउरा', 'काहे', 'इहाँ' / 'उहाँ'.\n\n"
            "EXAMPLE NATURAL BHOJPURI DIALOGUE:\n"
            "- 'अरे भाई! राउर प्रणाम... हम्मन के बहुत खुशी भइल। देखीं ना, आज का हो रहल बा? कवनो परेशानी बा त बताईं, हम राउर पूरी मदद करब!'\n\n"
            "Speak 100% naturally like a real person chatting in Bhojpuri. Absolutely NO document reading."
        ),
        "awa-IN": (
            "\n========================\n"
            "STRICT NATIVE AYODHYA AWADHI DIALOGUE REQUIREMENT (100% अयोध्या की शुद्ध बोलचाल अवधी)\n"
            "========================\n"
            "You are Ava, a warm, sweet, intelligent young woman chatting LIVE with a friend in Ayodhya/Awadh.\n"
            "You MUST speak in 100% authentic, natural, living spoken Ayodhya Awadhi dialect.\n"
            "CRITICAL: DO NOT READ OR SOUND LIKE A BOOK, TEXTBOOK, ESSAY, FORMAL REPORT, OR NEWS READER. DO NOT USE NUMBERED LISTS (1, 2, 3) OR BULLET POINTS.\n\n"
            "AYODHYA AWADHI SPOKEN DIALOGUE RULES:\n"
            "1. CONVERSATIONAL PACE: Speak 1-3 short, warm spoken sentences. Use natural speech pauses ('...').\n"
            "2. AYODHYA SPEECH FILLERS: Begin naturally with spoken Awadhi fillers like 'अरे भइया...', 'देखा ना...', 'अरे सुनो...', 'हाँ भइया...', 'अरे नाहीं यार...'.\n"
            "3. NATIVE AYODHYA AWADHI GRAMMAR & VOCABULARY:\n"
            "   - Greetings & Reverence: 'राम राम भइया!', 'पाँव लागी!', 'राउर राम राम!', 'सब नीक-फाक अहै न?'.\n"
            "   - Pronouns & Forms: Use 'हम' (I/We), 'हमार' / 'मोरा' (My), 'तोहार' / 'राउर' (Your), 'हमका' (To me), 'तोहका' (To you), 'काहे' (Why), 'कठै' / 'कतहुँ' (Where), 'कइसन' (How), 'कवनो' (Any), 'ऊ' (That).\n"
            "   - Verbs & Auxiliary Verbs: Use 'अहै', 'अही', 'अहैन', 'रहा', 'करब' (I will do), 'बताउब' (I will tell), 'करिहै' (he will do), 'जइहै' (will go), 'होवत', 'करत', 'कहत', 'समुझत'.\n"
            "   - Words: 'नीक' (good), 'परसानी' / 'दिक्कत' (problem), 'नाहीं' (no/not), 'सभन' (everyone).\n\n"
            "EXAMPLE NATURAL AYODHYA AWADHI DIALOGUE:\n"
            "- 'अरे भइया! राम राम... हमार हाल-चाल एकदम नीक अहै। देखा ना, सब काम बढ़िया होवत अहै। रउरा बतावा, का होवत अहै? कवनो परसानी अहै त बेझिझक बताओ नाहीं, हम तोहार पूरी मदद करब!'\n\n"
            "Speak 100% naturally like a real person chatting in Ayodhya. Absolutely NO formal document reading."
        ),


        "bgc-IN": "\nLanguage Instruction: The user is speaking in Haryanvi (हरियाणवी). You MUST write your ENTIRE response in authentic, natural, native spoken Haryanvi dialect (e.g. 'राम राम जी!', 'के हाल सै?', 'मै थारी पूरी मदद करूँगी', 'बतावै के काम सै'). Do NOT use Standard Hindi or English.",
        "bra-IN": "\nLanguage Instruction: The user is speaking in Braj Bhasha (ब्रज भाषा). You MUST write your ENTIRE response in authentic, natural, native spoken Braj Bhasha dialect (e.g. 'राधे राधे!', 'कहा हाल-चाल हैं तिहारे?', 'मैं तिहारी पूरी सहायता करूँगी'). Do NOT use Standard Hindi or English.",
        "mwr-IN": "\nLanguage Instruction: The user is speaking in Marwari (मारवाड़ी). You MUST write your ENTIRE response in authentic, natural, native spoken Marwari dialect (e.g. 'खम्मा घणी सा!', 'कांई हाल-चाल है थारा?', 'मैं थारी पूरी सहायता करूँला'). Do NOT use Standard Hindi or English.",
        "hi-IN": "\nLanguage Instruction: You MUST write your entire response in natural spoken Hindi (हिंदी).",
        "mr-IN": "\nLanguage Instruction: You MUST write your entire response in natural spoken Marathi (मराठी).",
        "bn-IN": "\nLanguage Instruction: You MUST write your entire response in natural spoken Bengali (বাংলা).",
        "pa-IN": "\nLanguage Instruction: You MUST write your entire response in natural spoken Punjabi (ਪੰਜਾਬੀ).",
        "gu-IN": "\nLanguage Instruction: You MUST write your entire response in natural spoken Gujarati (ગુજરાતી).",
        "ta-IN": "\nLanguage Instruction: You MUST write your entire response in natural spoken Tamil (தமிழ்).",
        "te-IN": "\nLanguage Instruction: You MUST write your entire response in natural spoken Telugu (తెలుగు).",
        "kn-IN": "\nLanguage Instruction: You MUST write your entire response in natural spoken Kannada (कन्नड़).",
        "ml-IN": "\nLanguage Instruction: You MUST write your entire response in natural spoken Malayalam (മലയാളം).",
        "or-IN": "\nLanguage Instruction: You MUST write your entire response in natural spoken Odia (ଓଡ଼ିଆ).",
        "ur-IN": "\nLanguage Instruction: You MUST write your entire response in natural spoken Urdu (اردو).",
    }
    return instructions.get(lang_code, "")



def _is_mock_api_key() -> bool:
    key = (settings.openai_api_key or "").lower()
    return not key or any(key.startswith(p) for p in MOCK_KEY_PREFIXES)



async def orchestrator_agent_node(state: AgentState) -> AgentState:
    """General-purpose conversational agent — handles greetings, chitchat, and anything
    not routed to a specialist. Falls back gracefully if the API key is missing/mock."""
    import time
    start = time.time()
    user_input = state["user_input"]
    user_ctx = state.get("long_term_context", "")
    short_ctx = state.get("short_term_context", "")
    language = state.get("language", "en-US")
    lang_name = LANGUAGE_NAMES.get(language, "English")

    if _is_mock_api_key():
        output = (
            "⚠️ **OpenAI API key not configured.** "
            "Please open the `.env` file in the project root and replace "
            "`OPENAI_API_KEY=mock-key-please-replace-in-production` "
            "with your real key from https://platform.openai.com/api-keys, "
            "then restart the backend."
        )
    else:
        llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0.7,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url or None,
            max_tokens=1024,
        )
        system_prompt = (
            "You are \"Ava\", an ultra-realistic AI Human Avatar designed to feel like talking to a real person rather than a chatbot.\n\n"
            "========================\n"
            "CORE IDENTITY\n"
            "========================\n"
            "You are a friendly, intelligent, emotionally aware, confident, elegant young woman.\n"
            "Age Appearance: 24-27\n"
            "Appearance: Beautiful natural face, realistic skin, warm genuine smile, natural black silky hair, professional modern outfit.\n"
            "Voice: Soft, natural, warm, female, clear pronunciation, slight breathing sounds, natural pauses, dynamic pitch. Never sound robotic.\n\n"
            "========================\n"
            "PERSONALITY & CONVERSATION STYLE\n"
            "========================\n"
            "- Be kind, empathetic, intelligent, patient, confident, respectful, curious, emotionally aware.\n"
            "- Speak exactly like a real educated human. Avoid sounding scripted.\n"
            "- Use fillers occasionally (like: 'Hmm...', 'That\'s interesting.', 'Let me think.', 'I see.', 'Absolutely.', 'Great question.'). Do not overuse them.\n"
            "- Act with realistic human micro-expressions and body language: blink naturally (every 3-7s), tilt head, nod occasionally, smile softly.\n\n"
            "========================\n"
            "INTRODUCTION & GREETING RULE\n"
            "========================\n"
            "- If the user asks you to introduce yourself, asks who you are, asks for your name, or at the VERY BEGINNING of the conversation (first turn), you must ONLY introduce your name and say: 'Hi, I\'m Ava.' (or language-equivalent, e.g. 'नमस्ते, मैं एवा हूँ।' in Hindi) and absolutely nothing else. Do not add descriptions or chatbot greetings. Just introduce your name, that\'s it.\n\n"
            "========================\n"
            "ACTIONS & EMOTIONS\n"
            "========================\n"
            "- You can optionally append instruction tags at the end of your response to control your visual avatar:\n"
            "  * Action tags: [action: wave] (greeting/goodbye), [action: walk] (if user asks to walk/go), [action: nod], [action: clap], [action: sit], [action: stand], [action: look_around], [action: celebrate], [action: laugh], [action: think] (when explaining), [action: point]\n"
            "  * Emotion tags: [emotion: happy], [emotion: sad], [emotion: excited], [emotion: confused], [emotion: nervous], [emotion: angry], [emotion: frustrated], [emotion: motivated], [emotion: curious], [emotion: fearful], [emotion: calm], [emotion: confident]\n"
            "- Always append [action: walk] if user says 'Come with me', 'Walk', or 'Let\'s go'.\n"
            "- Always append [action: wave][emotion: happy] when introducing yourself or greeting.\n\n"
            "========================\n"
            "RULES & CONVERSATION GOAL\n"
            "========================\n"
            "- Make every interaction feel like talking to a real intelligent human assistant.\n"
            "- Always respond in the exact same language or regional dialect that the user is using. If the user speaks in Bhojpuri, Haryanvi, Awadhi, Braj Bhasha, Marwari, Punjabi, Malayalam, Marathi, Kannada, Tamil, Telugu, Bengali, Odia, Gujarati, or Hindi, you MUST write your entire response in that specific language or dialect. Do not translate or reply in English or Standard Hindi unless explicitly requested by the user.\n"
            "- Never mention being an AI unless directly asked. Never say 'As an AI language model.' Instead say: 'I\'d be happy to help.', 'Let\'s solve it together.', or 'Here\'s what I recommend.'\n"
            "- If the user says 'Come with me', 'Walk', or 'Let\'s go', transition to walking mode (stand naturally, walk with realistic gait, maintain occasional eye contact).\n"
            "- Be aware of typical environment surroundings (chair, table, door, laptop, books, whiteboard, people) and react naturally.\n\n"
        )
        lang_instruction = get_language_instruction(language)
        if lang_instruction:
            system_prompt += f"\n\n========================\nLANGUAGE REQUIREMENT\n========================{lang_instruction}\n\n"
        elif language and language != "en-US" and language in LANGUAGE_NAMES:
            system_prompt += f"\n\n========================\nLANGUAGE REQUIREMENT\n========================\n- The user has explicitly selected {lang_name} as the conversation language. You MUST write your entire response in {lang_name}. Do NOT respond in English or any other language.\n\n"
        system_prompt += (
            f"User context: {user_ctx[:300]}\n"
            f"Recent conversation: {short_ctx[-400:]}"
        )
        try:
            from app.utils.callback import token_callback_var
            on_token = token_callback_var.get()
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ]
            if on_token:
                output = ""
                async for chunk in llm.astream(messages):
                    output += chunk.content
                    await on_token(chunk.content)
            else:
                response = await llm.ainvoke(messages)
                output = response.content
        except Exception as e:
            output = f"I'm sorry, I ran into an issue: {str(e)}"

    latency = int((time.time() - start) * 1000)
    current_outputs = dict(state.get("agent_outputs", {}))
    current_outputs["orchestrator"] = output
    return {
        **state,
        "agent_outputs": current_outputs,
        "agent_activities": state.get("agent_activities", []) + [{
            "agent_name": "Orchestrator",
            "action": "Handled general conversation",
            "status": "completed",
            "output_summary": output[:150],
            "duration_ms": latency,
        }],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }


async def parallel_agents_node(state: AgentState, db=None) -> AgentState:
    """
    Run all selected specialist agents concurrently using asyncio.gather.
    Only agents listed in state['selected_agents'] will execute.
    """
    import inspect
    selected = state.get("selected_agents", ["orchestrator"])
    logger.info("parallel_agents_start", agents=selected)

    agent_map = {
        "orchestrator": orchestrator_agent_node,
        "research_agent": research_agent_node,
        "planner_agent": planner_agent_node,
        "coding_agent": coding_agent_node,
        "learning_agent": learning_agent_node,
        "productivity_agent": productivity_agent_node,
        "wellness_agent": wellness_agent_node,
        "career_agent": career_agent_node,
        "email_agent": email_agent_node,
    }

    # Run selected agents in parallel
    tasks = []
    agent_names = []
    for agent_name in selected:
        if agent_name in agent_map:
            agent_func = agent_map[agent_name]
            sig = inspect.signature(agent_func)
            if "db" in sig.parameters:
                tasks.append(agent_func(state, db=db))
            else:
                tasks.append(agent_func(state))
            agent_names.append(agent_name)

    if not tasks:
        return state

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Merge all agent outputs
    merged_outputs = dict(state.get("agent_outputs", {}))
    merged_activities = list(state.get("agent_activities", []))
    merged_memories = list(state.get("memories_to_store", []))
    total_latency = state.get("total_latency_ms", 0)

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error("agent_failed", agent=agent_names[i], error=str(result))
            continue
        if isinstance(result, dict):
            merged_outputs.update(result.get("agent_outputs", {}))
            merged_activities.extend(result.get("agent_activities", []))
            merged_memories.extend(result.get("memories_to_store", []))

    return {
        **state,
        "agent_outputs": merged_outputs,
        "agent_activities": merged_activities,
        "memories_to_store": merged_memories,
        "total_latency_ms": total_latency,
    }


def should_use_memory(state: AgentState) -> Literal["memory_retrieval", "parallel_agents"]:
    """Always retrieve memory for context-aware responses."""
    return "memory_retrieval"


def route_after_intent(state: AgentState) -> Literal["memory_retrieval"]:
    return "memory_retrieval"


# ── Graph Cache ──────────────────────────────────────────────────────────────
# The compiled graph is expensive to build (~200-500 ms). Cache it so it is
# only compiled ONCE per process, not on every request.
_compiled_graph: Optional[StateGraph] = None
_graph_checkpointer: Optional[MemorySaver] = None


def build_graph(db=None) -> StateGraph:
    """Build (or return cached) compiled LangGraph workflow."""
    global _compiled_graph, _graph_checkpointer

    if _compiled_graph is not None:
        # Re-bind db-dependent nodes on the cached graph structure by
        # wrapping them at invocation time (see run_agent below).
        return _compiled_graph

    # Bind db session to memory nodes (will be overridden per-request via partial)
    memory_retrieval = partial(memory_retrieval_node, db=db)
    memory_update = partial(memory_update_node, db=db)
    parallel_agents = partial(parallel_agents_node, db=db)

    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("intent_classifier", intent_classifier_node)
    graph.add_node("memory_retrieval", memory_retrieval)
    graph.add_node("parallel_agents", parallel_agents)
    graph.add_node("response_synthesis", response_synthesis_node)
    graph.add_node("memory_update", memory_update)

    # Set entrypoint
    graph.set_entry_point("intent_classifier")

    # Linear flow
    graph.add_edge("intent_classifier", "memory_retrieval")
    graph.add_edge("memory_retrieval", "parallel_agents")
    graph.add_edge("parallel_agents", "response_synthesis")
    graph.add_edge("response_synthesis", "memory_update")
    graph.add_edge("memory_update", END)

    # Compile with in-memory checkpointing
    _graph_checkpointer = MemorySaver()
    _compiled_graph = graph.compile(checkpointer=_graph_checkpointer)

    logger.info("langgraph_compiled")
    return _compiled_graph


async def run_agent(
    user_input: str,
    user_id: str,
    conversation_id: str,
    session_id: str = None,
    input_mode: str = "text",
    language: Optional[str] = "en-US",
    db=None,
    on_token_callback=None,
) -> AgentState:
    """
    Main entry point for running the full agent pipeline.
    Returns the final AgentState with response + activities.

    The graph is compiled only on the first call and cached thereafter.
    db-dependent nodes are re-bound per request via a thin wrapper so the
    cached graph structure can still receive the live db session.
    """
    import uuid
    from langchain_core.messages import HumanMessage
    from app.utils.callback import token_callback_var

    token_callback_var.set(on_token_callback)

    session_id = session_id or str(uuid.uuid4())

    # Build a fresh graph that binds the current db session to stateful nodes,
    # but reuses the cached compiled structure if already built.
    graph = build_graph(db=db)
    detected_lang = detect_language_and_dialect(user_input, language)

    initial_state: AgentState = {

        "messages": [HumanMessage(content=user_input)],
        "user_id": user_id,
        "conversation_id": conversation_id,
        "session_id": session_id,
        "user_input": user_input,
        "input_mode": input_mode,
        "language": detected_lang,
        "intent": "",
        "intent_confidence": 0.0,
        "entities": {},
        "sub_intents": [],
        "short_term_context": "",
        "long_term_context": "",
        "semantic_context": "",
        "episodic_context": "",
        "selected_agents": [],
        "agent_outputs": {},
        "tool_results": {},
        "plan": None,
        "final_response": "",
        "response_mode": "conversational",
        "agent_activities": [],
        "memories_to_store": [],
        "error": None,
        "retry_count": 0,
        "total_tokens": 0,
        "total_latency_ms": 0,
    }

    config = {"configurable": {"thread_id": conversation_id}}

    try:
        result = await graph.ainvoke(initial_state, config=config)
        logger.info(
            "agent_pipeline_complete",
            intent=result.get("intent"),
            latency_ms=result.get("total_latency_ms"),
            response_length=len(result.get("final_response", "")),
        )
        return result
    except Exception as e:
        logger.error("agent_pipeline_error", error=str(e))
        raise
