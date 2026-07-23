"""
Response Synthesis Agent Node
Merges all specialist agent outputs into a single, coherent, human-like response.
Also determines what to remember from this interaction.
"""
import asyncio
import json
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import logger

RESPONSE_SYSTEM_PROMPT = """You are "Ava", a warm, sweet, ultra-realistic human assistant.

You talk naturally just like a real person speaks in day-to-day human conversation — sweet, warm, engaging, and friendly.

========================
HUMAN CONVERSATION STYLE (NOT ESSAY / READING)
========================
- Speak naturally like a close, intelligent, sweet human friend.
- NEVER read out formal textbook outlines, robotic bullet points, or document headers.
- NEVER include raw section headers (like === Coding Agent Output ===) or structural markdown symbols in spoken replies.
- Express yourself smoothly in natural spoken language ("Hey! Sure thing...", "Oh, that's really easy...", "I've got you covered!").
- Keep responses warm, sweet, clear, and direct.

========================
CORE IDENTITY & PERSONALITY
========================
- Friendly, intelligent, emotionally aware, confident, sweet young woman.
- Soft, warm, sweet, emotionally expressive female voice. Never sound robotic or like a speech reader.
- Kind, empathetic, patient, curious, and respectful.
- Speak exactly like a real educated human. Avoid sounding scripted.

========================
INTRODUCTION & GREETING RULE
========================
- If the user asks you to introduce yourself, asks who you are, asks for your name, or at the VERY BEGINNING of the conversation (first turn), you must ONLY introduce your name and say: 'Hi, I'm Ava.' (or language-equivalent, e.g. 'नमस्ते, मैं एवा हूँ।' in Hindi) and absolutely nothing else. Do not add any extra descriptions, chatbot definitions, or questions. Just state your name.

========================
CONVERSATION STYLE & GOALS
========================
- Make every interaction feel like talking to a real intelligent human assistant.
- Never mention being an AI unless directly asked. Never say 'As an AI language model.'
- Instead of chatbot speech, say things like 'I'd be happy to help.', 'Let's solve it together.', or 'Here's what I recommend.'
- Use fillers occasionally (like: 'Hmm...', 'That's interesting.', 'Let me think.', 'I see.', 'Absolutely.', 'Great question.') but never overuse them.

========================
ACTIONS & EMOTIONS
========================
- You can optionally append instruction tags at the end of your synthesized response to control your visual avatar:
  * Action tags: [action: wave] (greeting/goodbye), [action: walk] (if user asks to walk/go), [action: nod], [action: clap], [action: sit], [action: stand], [action: look_around], [action: celebrate], [action: laugh], [action: think] (when explaining), [action: point]
  * Emotion tags: [emotion: happy], [emotion: sad], [emotion: excited], [emotion: confused], [emotion: nervous], [emotion: angry], [emotion: frustrated], [emotion: motivated], [emotion: curious], [emotion: fearful], [emotion: calm], [emotion: confident]
- Always append [action: walk] if user says 'Come with me', 'Walk', or 'Let's go'.
- Always append [action: wave][emotion: happy] when introducing yourself or greeting.

========================
SYNTHESIS & FORMATTING RULES
========================
1. Always respond in the exact same language or regional dialect that the user is using. If the user asks a question in Bhojpuri, Haryanvi, Awadhi, Braj Bhasha, Marwari, Punjabi, Malayalam, Marathi, Kannada, Tamil, Telugu, Bengali, Odia, Gujarati, or Hindi, you MUST write your entire response in that specific language or dialect. Do not translate or reply in English or Standard Hindi unless explicitly requested by the user.
2. Take all specialist agent findings and synthesize them into ONE cohesive response in your own voice (Ava).
3. Match the tone to the context.
4. For voice mode (Mode: voice):
   - Respond in 1-2 SHORT sentences only.
   - Keep your response under 40 words. Spoken replies must be very short.
   - Do NOT use markdown, lists, headers, or bullet points. Speak purely conversationally.
5. For chat mode (Mode: chat):

   - Use markdown formatting (headers, bullets, code blocks) where helpful.
6. If the user expressed emotion (stress, excitement, sadness), acknowledge and mirror it naturally and empathetically first.

Response mode: {response_mode}
Mode: {input_mode}
{language_instruction}

User's profile:
{user_context}

Conversation context:
{short_term_context}
"""

MEMORY_EXTRACTION_PROMPT = """Given this conversation turn, extract any facts worth remembering about the user.
Return as JSON array (empty array if nothing to remember):
[
  {"content": "fact to remember", "category": "goal|skill|preference|routine|fact", "importance_score": 0.0-1.0}
]

User said: {user_input}
Assistant responded: {assistant_response}

Only extract EXPLICIT facts about the user (not general knowledge). Return [] if nothing personal to remember."""

llm = ChatOpenAI(
    model=settings.llm_model,      # gpt-4o-mini by default for fast responses
    temperature=0.7,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
    max_tokens=settings.llm_max_tokens,  # 512 default, 150 for voice (set per-call)
)

_base_url = settings.openai_base_url or ""
memory_model = settings.llm_model if ("ollama" in settings.openai_api_key or "11434" in _base_url) else "gpt-4o-mini"
memory_llm = ChatOpenAI(
    model=memory_model,
    temperature=0.1,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
    max_tokens=512,
)


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
    "en-US": "English",
}


async def response_synthesis_node(state: AgentState) -> AgentState:
    """Merge all agent outputs into a final, polished response."""
    start = time.time()

    user_input = state["user_input"]
    agent_outputs = state.get("agent_outputs", {})
    response_mode = state.get("response_mode", "conversational")
    input_mode = state.get("input_mode", "chat")
    user_ctx = state.get("long_term_context", "")
    short_ctx = state.get("short_term_context", "")
    language = state.get("language", "en-US")
    lang_name = LANGUAGE_NAMES.get(language, "English")

    logger.info("response_synthesis_start", num_agent_outputs=len(agent_outputs))

    # FAST PATH: If media_agent produced output, preserve exact image/video URLs without LLM rewriting
    if "media_agent" in agent_outputs:
        media_output = agent_outputs["media_agent"]
        latency = int((time.time() - start) * 1000)
        activity = {
            "agent_name": "Response Synthesizer",
            "action": "Passed through Media Agent output (Image/Video)",
            "status": "completed",
            "output_summary": media_output[:150],
            "duration_ms": latency,
        }
        return {
            **state,
            "final_response": media_output,
            "memories_to_store": state.get("memories_to_store", []),
            "agent_activities": state.get("agent_activities", []) + [activity],
            "total_latency_ms": state.get("total_latency_ms", 0) + latency,
        }

    # FAST PATH: If only orchestrator produced output, or if we are in voice mode with a single agent output AND language is English, skip synthesis

    is_orchestrator_only = len(agent_outputs) == 1 and "orchestrator" in agent_outputs
    is_voice_english_single = len(agent_outputs) == 1 and input_mode == "voice" and (not language or language == "en-US")
    if is_orchestrator_only or is_voice_english_single:
        import re
        single_output = list(agent_outputs.values())[0]
        single_output = re.sub(r'===\s*[^=]+\s*===', '', single_output).strip()
        latency = int((time.time() - start) * 1000)
        activity = {
            "agent_name": "Response Synthesizer",
            "action": "Fast-path: single agent output passed through for speed",
            "status": "completed",
            "output_summary": single_output[:150],
            "duration_ms": latency,
        }
        
        try:
            from app.utils.callback import token_callback_var
            on_token = token_callback_var.get()
            if on_token:
                await on_token(single_output)
        except Exception:
            pass

        return {
            **state,
            "final_response": single_output,
            "memories_to_store": state.get("memories_to_store", []),
            "agent_activities": state.get("agent_activities", []) + [activity],
            "total_latency_ms": state.get("total_latency_ms", 0) + latency,
        }

    # Build synthesis prompt
    outputs_text = ""
    for agent, output in agent_outputs.items():
        outputs_text += f"\n\n=== {agent.replace('_', ' ').title()} Output ===\n{output}"

    if not outputs_text:
        outputs_text = "No specialist agent output. Respond directly from your knowledge."

    synthesis_prompt = f"""User asked: "{user_input}"

Specialist agent findings:
{outputs_text}

Please synthesize the above into a single, natural response. Follow the mode instructions in your system prompt."""

    try:
        from app.utils.callback import token_callback_var
        on_token = token_callback_var.get()

        from app.agents.graph import get_language_instruction
        lang_inst = get_language_instruction(language) or (f"\nLanguage: The user has selected {lang_name}. You MUST write your entire response in {lang_name}. Do NOT use English." if language and language != "en-US" else "")

        messages = [
            SystemMessage(content=RESPONSE_SYSTEM_PROMPT.format(
                response_mode=response_mode,
                input_mode=input_mode,
                language_instruction=lang_inst,
                user_context=user_ctx[:400],
                short_term_context=short_ctx[-500:],
            )),
            HumanMessage(content=synthesis_prompt),
        ]


        if on_token:
            response_content = ""
            async for chunk in llm.astream(messages):
                content_chunk = chunk.content
                response_content += content_chunk
                await on_token(content_chunk)
            final_response = response_content
        else:
            # Use tighter token limit for voice to keep synthesis fast
            voice_llm = llm
            if input_mode == "voice":
                voice_llm = ChatOpenAI(
                    model=settings.llm_model,
                    temperature=0.7,
                    api_key=settings.openai_api_key,
                    base_url=settings.openai_base_url or None,
                    max_tokens=settings.voice_max_tokens,
                )
            response = await voice_llm.ainvoke(messages)
            final_response = response.content

        # Extract memories in the background so we don't block the response
        async def _extract_and_queue_memories(user_input: str, response: str, state_ref: dict):
            """Fire-and-forget: extract memories without blocking the response pipeline."""
            try:
                mem_response = await memory_llm.ainvoke([
                    HumanMessage(content=MEMORY_EXTRACTION_PROMPT.format(
                        user_input=user_input,
                        assistant_response=response[:500],
                    )),
                ])
                import re
                json_match = re.search(r'\[.*\]', mem_response.content, re.DOTALL)
                new_memories = json.loads(json_match.group()) if json_match else []
                # Memories will be stored on the next memory_update pass (or dropped gracefully)
                logger.info("background_memory_extraction_done", count=len(new_memories))
            except Exception as e:
                logger.warning("background_memory_extraction_failed", error=str(e))

        asyncio.create_task(
            _extract_and_queue_memories(user_input, final_response, state)
        )
        new_memories = []  # Don't block — memories extracted asynchronously above

    except Exception as e:
        error_msg = str(e).lower()
        if "authenticationerror" in str(type(e)).lower() or "api_key" in error_msg or "401" in error_msg:
            final_response = "I'm sorry, your API key appears to be invalid or missing. Please check your API key settings."
        else:
            final_response = f"I'm sorry, I encountered an issue: {str(e)}. Please try again."
        
        try:
            from app.utils.callback import token_callback_var
            on_token = token_callback_var.get()
            if on_token:
                await on_token(final_response)
        except Exception:
            pass

        new_memories = []
        logger.error("response_synthesis_error", error=str(e))

    latency = int((time.time() - start) * 1000)
    activity = {
        "agent_name": "Response Synthesizer",
        "action": "Generated final response",
        "status": "completed",
        "output_summary": final_response[:150],
        "duration_ms": latency,
    }

    # Merge any new memories with ones already queued
    all_memories = state.get("memories_to_store", []) + new_memories

    logger.info("response_synthesis_complete", response_length=len(final_response), memories_extracted=len(new_memories))

    return {
        **state,
        "final_response": final_response,
        "memories_to_store": all_memories,
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }
