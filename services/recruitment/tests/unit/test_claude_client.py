"""
Unit tests for ClaudeClient.
Tests the field allowlist, fenced-JSON parsing, and per-method routing
without making real API calls — anthropic.Anthropic is monkeypatched.

This covers the highest-risk code: the fenced-JSON stripper that was
introduced to fix Claude's tendency to wrap JSON in markdown code fences.
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from shared.ai_client.claude_client import ClaudeClient
from shared.ai_client.constraints import AIConstraints, ANALYZE_BIAS_DEEP

DUMMY_KEY = "sk-ant-test000"


# ── helpers ───────────────────────────────────────────────────────────────────

def _client_with_response(text: str) -> ClaudeClient:
    """
    Return a ClaudeClient whose underlying Anthropic SDK always returns
    the given text as the first content block.
    """
    with patch("shared.ai_client.claude_client.anthropic.Anthropic") as MockAnthropic:
        client = ClaudeClient(DUMMY_KEY)
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=text)]
        client._client.messages.create.return_value = mock_msg
    return client


_SIMPLE_CONSTRAINT = AIConstraints(
    operation="test_op",
    allowed_fields=("field_a", "field_b"),
    max_tokens=100,
    system_prompt="test prompt",
)


# ── fenced-JSON parsing ───────────────────────────────────────────────────────

class TestFencedJsonParsing:
    """
    Claude sometimes wraps responses in markdown code fences even when
    instructed to return raw JSON.  The call() method must strip them.
    """

    def test_plain_json_is_parsed(self):
        client = _client_with_response('{"flagged": false}')
        result = client.call(_SIMPLE_CONSTRAINT, {"field_a": "x"})
        assert result == {"flagged": False}

    def test_fenced_json_block_is_stripped(self):
        fenced = "```json\n{\"flagged\": true}\n```"
        client = _client_with_response(fenced)
        result = client.call(_SIMPLE_CONSTRAINT, {"field_a": "x"})
        assert result == {"flagged": True}

    def test_plain_fence_without_language_tag_is_stripped(self):
        fenced = "```\n{\"ok\": 1}\n```"
        client = _client_with_response(fenced)
        result = client.call(_SIMPLE_CONSTRAINT, {"field_a": "x"})
        assert result == {"ok": 1}

    def test_fenced_json_with_complex_payload_is_parsed(self):
        payload = {"flagged": True, "phrases": [{"phrase": "ninja", "reason": "exclusionary"}]}
        fenced = f"```json\n{json.dumps(payload)}\n```"
        client = _client_with_response(fenced)
        result = client.call(_SIMPLE_CONSTRAINT, {"field_a": "x"})
        assert result["flagged"] is True
        assert result["phrases"][0]["phrase"] == "ninja"

    def test_response_with_leading_trailing_whitespace_is_parsed(self):
        client = _client_with_response('  \n{"ok": 2}\n  ')
        result = client.call(_SIMPLE_CONSTRAINT, {"field_a": "x"})
        assert result == {"ok": 2}


# ── field allowlisting ────────────────────────────────────────────────────────

class TestFieldAllowlist:
    """Only fields in constraints.allowed_fields must be sent to Claude."""

    def test_allowed_fields_are_included(self):
        client = _client_with_response('{"ok": true}')
        client.call(_SIMPLE_CONSTRAINT, {"field_a": "keep_me", "field_b": "also_keep"})
        call_kwargs = client._client.messages.create.call_args
        sent = json.loads(call_kwargs.kwargs["messages"][0]["content"])
        assert "field_a" in sent
        assert "field_b" in sent

    def test_non_allowed_fields_are_stripped(self):
        client = _client_with_response('{"ok": true}')
        client.call(_SIMPLE_CONSTRAINT, {"field_a": "keep", "secret_pii": "strip_me"})
        call_kwargs = client._client.messages.create.call_args
        sent = json.loads(call_kwargs.kwargs["messages"][0]["content"])
        assert "secret_pii" not in sent

    def test_entirely_disallowed_payload_sends_empty_object(self):
        client = _client_with_response('{"ok": true}')
        client.call(_SIMPLE_CONSTRAINT, {"disallowed_key": "value"})
        call_kwargs = client._client.messages.create.call_args
        sent = json.loads(call_kwargs.kwargs["messages"][0]["content"])
        assert sent == {}


# ── constraint routing ────────────────────────────────────────────────────────

class TestConstraintRouting:
    """Each convenience method must route to its correct constraint."""

    def test_analyze_bias_sends_text_and_context(self):
        client = _client_with_response('{"flagged": false, "phrases": [], "overall_suggestion": null}')
        client.analyze_bias("some text", "job_posting")
        call_kwargs = client._client.messages.create.call_args
        sent = json.loads(call_kwargs.kwargs["messages"][0]["content"])
        assert sent["text"] == "some text"
        assert sent["context"] == "job_posting"

    def test_analyze_bias_uses_analyze_bias_deep_constraint(self):
        client = _client_with_response('{"flagged": false, "phrases": [], "overall_suggestion": null}')
        client.analyze_bias("text")
        call_kwargs = client._client.messages.create.call_args
        assert call_kwargs.kwargs["max_tokens"] == ANALYZE_BIAS_DEEP.max_tokens
        assert "bias" in call_kwargs.kwargs["system"].lower()

    def test_analyze_bias_default_context_is_general(self):
        client = _client_with_response('{"flagged": false, "phrases": [], "overall_suggestion": null}')
        client.analyze_bias("text")
        call_kwargs = client._client.messages.create.call_args
        sent = json.loads(call_kwargs.kwargs["messages"][0]["content"])
        assert sent["context"] == "general"


# ── AbstractAIClient conformance ──────────────────────────────────────────────

class TestAbstractClientConformance:
    """ClaudeClient must fully implement AbstractAIClient."""

    def test_claude_client_is_abstract_ai_client_subclass(self):
        from shared.ai_client.abstract_client import AbstractAIClient
        assert issubclass(ClaudeClient, AbstractAIClient)

    def test_claude_client_can_be_instantiated(self):
        with patch("shared.ai_client.claude_client.anthropic.Anthropic"):
            client = ClaudeClient(DUMMY_KEY)
        assert client is not None
