"""
Research Agent Node
Web search + RAG-based information gathering.
Tools: Tavily web search, knowledge base retrieval.
"""
import time
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from app.agents.state import AgentState
from app.config import settings
from app.utils.logger import logger

RESEARCH_SYSTEM_PROMPT = """You are a research specialist AI. Your job is to:
1. Search the web for accurate, up-to-date information
2. Synthesize findings from multiple sources
3. Verify facts and cross-reference information
4. Present findings in a clear, structured way

Always cite your sources. Be thorough but concise.
If asked about recent events, prioritize the most recent information.

Context from user's memory:
{memory_context}
"""

llm = ChatOpenAI(
    model=settings.llm_model,
    temperature=0.3,
    api_key=settings.openai_api_key,
    base_url=settings.openai_base_url or None,
)


async def research_agent_node(state: AgentState) -> AgentState:
    """Conduct web research and return synthesized findings."""
    if "research_agent" not in state.get("selected_agents", []):
        return state

    start = time.time()
    user_input = state["user_input"]
    memory_ctx = f"{state.get('long_term_context', '')}\n{state.get('semantic_context', '')}"

    logger.info("research_agent_start", query=user_input[:100])

    tool_results = []
    sources = []
    action_taken = "Performed web research"
    lowered_input = user_input.lower()

    # 1. Check for Math / Calculation
    if any(k in lowered_input for k in ["calculate", "solve", "math", "calculator", "compute", "what is 2", "plus", "minus"]):
        try:
            from app.tools.calculator import calculate
            import json
            import re
            extraction_prompt = f"""
            Extract the exact mathematical expression to compute from the user input.
            User input: "{user_input}"
            
            Respond ONLY with a JSON object:
            {{
                "expression": "math expression to evaluate"
            }}
            """
            extraction_resp = await llm.ainvoke(extraction_prompt)
            match = re.search(r'\{.*\}', extraction_resp.content, re.DOTALL)
            if match:
                expr = json.loads(match.group()).get("expression")
                if expr:
                    res = calculate(expr)
                    tool_results.append(f"Math Calculation: {res}")
                    action_taken = "Evaluated math expression"
        except Exception as e:
            logger.warning("research_agent_calculator_error", error=str(e))

    # 2. Check for Weather
    if not tool_results and any(k in lowered_input for k in ["weather", "temperature", "forecast", "rain in", "sunny in"]):
        try:
            from app.tools.weather import get_weather
            import json
            import re
            extraction_prompt = f"""
            Extract the city/location name for which weather info is requested.
            User input: "{user_input}"
            
            Respond ONLY with a JSON object:
            {{
                "location": "city name and optionally country"
            }}
            """
            extraction_resp = await llm.ainvoke(extraction_prompt)
            match = re.search(r'\{.*\}', extraction_resp.content, re.DOTALL)
            if match:
                loc = json.loads(match.group()).get("location")
                if loc:
                    res = await get_weather(loc)
                    tool_results.append(f"Weather Check: {res}")
                    action_taken = f"Checked weather for {loc}"
        except Exception as e:
            logger.warning("research_agent_weather_error", error=str(e))

    # 3. Check for File Reading
    if not tool_results and any(k in lowered_input for k in ["read file", "open file", "view file", "show file", "content of"]):
        try:
            from app.tools.file_reader import read_file_content
            import json
            import re
            extraction_prompt = f"""
            Extract the full file path from the user input.
            User input: "{user_input}"
            
            Respond ONLY with a JSON object:
            {{
                "file_path": "path to file"
            }}
            """
            extraction_resp = await llm.ainvoke(extraction_prompt)
            match = re.search(r'\{.*\}', extraction_resp.content, re.DOTALL)
            if match:
                path = json.loads(match.group()).get("file_path")
                if path:
                    res = read_file_content(path)
                    tool_results.append(f"File Reader Result:\n{res}")
                    filename = os.path.basename(path) if '/' in path or '\\' in path else path
                    action_taken = f"Read file: {filename}"
        except Exception as e:
            logger.warning("research_agent_file_reader_error", error=str(e))

    # 4. Fallback/Default: Web search via Tavily
    if not tool_results and settings.tavily_api_key:
        try:
            search_tool = TavilySearchResults(
                max_results=5,
                api_key=settings.tavily_api_key,
            )
            results = await search_tool.ainvoke({"query": user_input})

            search_results = ""
            if isinstance(results, list):
                for r in results:
                    if isinstance(r, dict):
                        sources.append(r.get("url", ""))
                        search_results += f"\n\nSource: {r.get('url', 'N/A')}\n{r.get('content', '')}"
            elif isinstance(results, str):
                search_results = results

            if search_results:
                tool_results.append(f"Web Search Results:\n{search_results}")
                action_taken = f"Searched web + synthesized {len(sources)} sources"
            
            logger.info("web_search_complete", num_sources=len(sources))
        except Exception as e:
            logger.warning("web_search_failed", error=str(e))
            tool_results.append(f"Web search unavailable: {str(e)}")

    # Synthesize findings with LLM
    tool_output_str = "\n\n".join(tool_results) if tool_results else "No external information available. Answer from your knowledge."
    synthesis_prompt = f"""
    User Question: {user_input}

    Gathered Information / Tool Output:
    {tool_output_str}

    Please synthesize the above information into a clear, accurate response.
    """

    try:
        response = await llm.ainvoke([
            SystemMessage(content=RESEARCH_SYSTEM_PROMPT.format(memory_context=memory_ctx[:500])),
            HumanMessage(content=synthesis_prompt),
        ])
        research_output = response.content
    except Exception as e:
        research_output = f"Research failed: {str(e)}"
        logger.error("research_synthesis_failed", error=str(e))

    latency = int((time.time() - start) * 1000)
    logger.info("research_agent_complete", latency_ms=latency)

    activity = {
        "agent_name": "Research Agent",
        "action": action_taken,
        "status": "completed",
        "input_summary": user_input[:100],
        "output_summary": research_output[:150],
        "duration_ms": latency,
    }

    current_outputs = state.get("agent_outputs", {})
    current_outputs["research_agent"] = research_output

    return {
        **state,
        "agent_outputs": current_outputs,
        "agent_activities": state.get("agent_activities", []) + [activity],
        "total_latency_ms": state.get("total_latency_ms", 0) + latency,
    }

