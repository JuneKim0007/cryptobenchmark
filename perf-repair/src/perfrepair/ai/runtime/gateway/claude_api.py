from __future__ import annotations

from ....dto.prompt import CorrectionPrompt, Lifetime, SystemPrompt, TaskPrompt
from ..agent.conversation import LifetimeGuarded
from ..agent.reply import AgentFailed, AgentRefused, AgentReply

DEFAULT_MODEL = "claude-opus-5-5"
MAX_TOKENS = 16000
# The Messages API answers 400 to string length limits, and to a {n,m} it finds too complex; the gate checks both.
API_UNSUPPORTED = ("maxLength", "minLength", "pattern")


def api_schema(node: dict) -> dict:
    out = {k: v for k, v in node.items() if k not in API_UNSUPPORTED}
    if "properties" in out:
        out["properties"] = {name: api_schema(child) for name, child in out["properties"].items()}
    if isinstance(out.get("items"), dict):
        out["items"] = api_schema(out["items"])
    return out


class _NoSdkError(Exception):
    pass


class ClaudeClient:

    def __init__(self, model: str = DEFAULT_MODEL, effort: str = "medium", max_tokens: int = MAX_TOKENS, client=None):
        self.model, self.effort, self.max_tokens = model, effort, max_tokens
        try:
            import anthropic
        except ImportError:
            if client is None:
                raise AgentFailed("claude_api_missing", "auth api needs the anthropic package: pip install -e .[api]") from None
            anthropic = None
        self.client = client or anthropic.Anthropic()
        # an injected client without the SDK raises nothing this class codes
        self.api_error = anthropic.APIError if anthropic else _NoSdkError

    def request(self, system: SystemPrompt, messages: list[dict], schema: dict) -> tuple[AgentReply, list]:
        block = {"type": "text", "text": system.text}
        # Only text that outlives one conversation repays a cache write.
        if system.lifetime is Lifetime.RUN:
            block["cache_control"] = {"type": "ephemeral"}
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=[block],
                messages=messages,
                output_config={"effort": self.effort, "format": {"type": "json_schema", "schema": api_schema(schema)}},
                # On a policy decline the API re-runs the request on a fallback model inside the same call.
                extra_headers={"anthropic-beta": "server-side-fallback-2026-07-01"},
                extra_body={"fallbacks": "default"},
            )
        except self.api_error as e:
            raise AgentFailed("claude_api_failed", " ".join(str(e).split())[:300]) from None
        if response.stop_reason == "refusal":
            raise AgentRefused(getattr(response.stop_details, "explanation", None) or "refused")
        text = next((b.text for b in response.content if b.type == "text"), "")
        u = response.usage
        return AgentReply(text, response.model, getattr(response, "_request_id", "") or "", {
            "input": u.input_tokens, "output": u.output_tokens,
            "cacheRead": getattr(u, "cache_read_input_tokens", 0) or 0,
            "cacheWrite": getattr(u, "cache_creation_input_tokens", 0) or 0,
        }), list(response.content)


class ClaudeConversation(LifetimeGuarded):

    def __init__(self, client: ClaudeClient, system: SystemPrompt, schema: dict):
        super().__init__(system)
        self.client, self.schema, self.messages = client, schema, []

    def _send(self, message: TaskPrompt | CorrectionPrompt) -> AgentReply:
        self.messages.append({"role": "user", "content": message.text})
        reply, content = self.client.request(self.system, self.messages, self.schema)
        # The whole content goes back, thinking blocks included: the API checks them on the next turn.
        self.messages.append({"role": "assistant", "content": content})
        return reply


class ClaudeConversations:

    def __init__(self, model: str = DEFAULT_MODEL, effort: str = "medium", max_tokens: int = MAX_TOKENS, client=None):
        self.client = ClaudeClient(model, effort, max_tokens, client)

    def start(self, system: SystemPrompt, schema: dict) -> ClaudeConversation:
        return ClaudeConversation(self.client, system, schema)
