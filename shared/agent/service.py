"""Facade used by HTTP and CLI."""

from __future__ import annotations

from orchestrator.registry import ProjectRegistry

from shared.agent.compiler import compile_natural_language
from shared.agent.schemas import (
    AgentCompileRequest,
    AgentCompileResponse,
    AgentValidateResponse,
    StandardVideoJobRequest,
)
from shared.agent.validate import validate_standard_request


def compile_request_body(
    body: AgentCompileRequest,
    registry: ProjectRegistry,
) -> AgentCompileResponse:
    if body.session_id and body.persist_turns:
        from shared.studio.services.intent_sessions import append_user_turn

        append_user_turn(body.session_id, body.prompt)

    res = compile_natural_language(
        body.prompt,
        registry,
        previous=body.previous,
    )

    if body.session_id and body.persist_turns:
        from shared.studio.services.intent_sessions import append_compile_turn

        snap = res.standard_request.model_dump_json() if res.success and res.standard_request else None
        append_compile_turn(
            body.session_id,
            prompt_snapshot=body.prompt,
            compile_response_json=res.model_dump_json(),
            standard_template_json=snap,
        )

    return res


def validate_body(
    req: StandardVideoJobRequest,
    registry: ProjectRegistry,
) -> AgentValidateResponse:
    return validate_standard_request(req, registry)
