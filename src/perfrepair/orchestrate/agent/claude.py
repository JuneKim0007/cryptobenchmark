"""The Messages API: one request builder, used as a single-call Agent and as a multi-turn Conversation."""
from __future__ import annotations

from .reply import AgentRefused, AgentReply


class ClaudeClient:
    """The system prompt is the same bytes on every request of a stage, so it is marked for caching;
    messages change every request and are never cached."""

    def __init__(self, model: str = "claude-opus-5-5", effort: str = "medium", max_tokens: int = 16000, client=None):
        import anthropic

        self.model, self.effort, self.max_tokens = model, effort, max_tokens
        self.client = client or anthropic.Anthropic()

    def request(self, system: str, messages: list[dict], schema: dict) -> tuple[AgentReply, list]:
        """The reply, and the response's content blocks to append to the history as they are."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=messages,
            output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": schema}},
            # On a policy decline the API re-runs the request on a fallback model inside the same call.
            extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
            extra_body={"fallbacks": "default"},
        )
        if response.stop_reason == "refusal":
            raise AgentRefused(getattr(response.stop_details, "explanation", None) or "refused")
        text = next((b.text for b in response.content if b.type == "text"), "")
        u = response.usage
        return AgentReply(text, response.model, getattr(response, "_request_id", "") or "", {
            "input": u.input_tokens, "output": u.output_tokens,
            "cacheRead": getattr(u, "cache_read_input_tokens", 0) or 0,
            "cacheWrite": getattr(u, "cache_creation_input_tokens", 0) or 0,
        }), list(response.content)


class ClaudeAgent:
    """Agent: one single-turn request per call."""

    def __init__(self, model: str = "claude-opus-5-5", effort: str = "medium", max_tokens: int = 16000, client=None):
        self.client = ClaudeClient(model, effort, max_tokens, client)

    def __call__(self, system: str, user: str, schema: dict) -> AgentReply:
        return self.client.request(system, [{"role": "user", "content": user}], schema)[0]
