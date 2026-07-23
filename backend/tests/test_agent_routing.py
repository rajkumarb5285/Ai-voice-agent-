"""
Unit tests for the intent classifier and multi-agent routing.
"""
import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.state import AgentState
from app.agents.intent_classifier import intent_classifier_node
from app.agents.graph import run_agent
from app.config import settings

@pytest.mark.asyncio
async def test_intent_classifier():
    """Verify intent classifier parses input and maps to correct agents."""
    initial_state = AgentState(
        user_input="Write a python binary search function.",
        messages=[],
        user_id="test-user-id",
        conversation_id="test-conv-id",
        session_id="test-session-id",
        input_mode="text",
        intent="",
        intent_confidence=0.0,
        entities={},
        sub_intents=[],
        short_term_context="",
        long_term_context="",
        semantic_context="",
        episodic_context="",
        selected_agents=[],
        agent_outputs={},
        tool_results={},
        plan=None,
        final_response="",
        response_mode="conversational",
        agent_activities=[],
        memories_to_store=[],
        error=None,
        retry_count=0,
        total_tokens=0,
        total_latency_ms=0
    )

    mock_llm_response = MagicMock()
    mock_llm_response.content = json.dumps({
        "intent": "coding",
        "confidence": 0.98,
        "sub_intents": ["python"],
        "entities": {"language": "python", "task": "binary search"},
        "selected_agents": ["coding_agent"],
        "response_mode": "structured"
    })

    with patch("langchain_openai.ChatOpenAI.ainvoke", new_callable=AsyncMock) as mock_invoke, \
         patch("app.agents.intent_classifier.classify_intent_by_keywords", return_value={"intent": "general_chat"}), \
         patch.object(settings, "fast_intent_classification", False), \
         patch.object(settings, "openai_api_key", "mock-key"), \
         patch.object(settings, "openai_base_url", "http://mock-url"):
        mock_invoke.return_value = mock_llm_response

        updated_state = await intent_classifier_node(initial_state)

        assert updated_state["intent"] == "coding"
        assert updated_state["intent_confidence"] == 0.98
        assert "coding_agent" in updated_state["selected_agents"]
        assert updated_state["response_mode"] == "structured"
        mock_invoke.assert_called_once()

@pytest.mark.asyncio
async def test_full_graph_routing(mock_db):
    """Verify the end-to-end graph execution runs classifier, specialist agent, and response synthesis."""
    mock_classifier_response = MagicMock(content=json.dumps({
        "intent": "research",
        "confidence": 0.95,
        "sub_intents": ["web_search"],
        "entities": {"query": "artificial intelligence"},
        "selected_agents": ["research_agent"],
        "response_mode": "conversational"
    }))

    mock_research_response = MagicMock(content="Here are details about AI.")
    mock_synthesis_response = MagicMock(content="According to the research, AI is developing rapidly.")

    # Patch the LLM calls globally via ChatOpenAI class ainvoke method
    with patch("langchain_openai.ChatOpenAI.ainvoke", new_callable=AsyncMock) as mock_llm, \
         patch("app.agents.intent_classifier.classify_intent_by_keywords", return_value={"intent": "general_chat"}), \
         patch.object(settings, "fast_intent_classification", False), \
         patch.object(settings, "openai_api_key", "mock-key"), \
         patch.object(settings, "openai_base_url", "http://mock-url"):
        mock_llm.side_effect = [
            mock_classifier_response,
            mock_research_response,
            mock_synthesis_response
        ]

        final_state = await run_agent(
            user_input="Search for latest developments in AI.",
            user_id=str(uuid_uuid := MagicMock(return_value="test-uuid")),
            conversation_id="test-conv-id",
            db=mock_db
        )

        assert final_state["intent"] == "research"
        assert "research_agent" in final_state["selected_agents"]
        assert "research_agent" in final_state["agent_outputs"]
        assert final_state["final_response"] == "According to the research, AI is developing rapidly."
