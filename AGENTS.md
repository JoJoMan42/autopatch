# AGENTS.md: rules for AI coding agents in PatchPilot

These rules apply to every AI tool working in this repository (Copilot, Cursor, Antigravity). The full specification is in `docs/SPEC.md`. The rationale is in `docs/DESIGN.md`. If a rule here conflicts with the spec, stop and ask the human.

## Scope of each task
- Work on exactly the files named in the task. Do not edit any other file.
- Implement a file only from its blueprint entry in `docs/SPEC.md` (Part 2). Do not invent extra classes, endpoints, or config keys.
- Do not change shared contracts (`backend/src/patchpilot/constants.py`, `backend/src/patchpilot/schemas/pipeline.py`, `shared/pp_contracts/src/pp_contracts/sandbox.py`, `backend/src/patchpilot/llm/types.py`) unless the task explicitly says so. If one must change, stop and report why.
- Never edit `docs/SPEC.md` or `docs/DESIGN.md`.
- Do not install new dependencies unless the task says so. Add them only to the `pyproject.toml` named in the spec.

## Layering and imports
- Routes (`api/routes/*`) call services only. Services call domain modules and the database. Domain modules never import from `api`.
- All model calls go through `LLMGateway` (`llm/gateway.py`). Never call an LLM provider directly.
- All container operations go through `sandbox_client/client.py`. Only `sandbox_runner` talks to Docker.
- All state changes go through `core/state_machine.py`. Never update a `state`, `status`, or `version` column directly.
- Database access is synchronous (SQLAlchemy 2.0 with psycopg 3). Only the WebSocket handler is async.

## Security rules (non-negotiable)
- Never use `shell=True`. Always pass commands as lists.
- Never use `eval`, `exec`, or `pickle.loads` on untrusted data.
- Never log source code, prompts, secrets, or tokens above DEBUG level. Use `core/redaction.py` before logging any external text.
- Never write files outside the workspace or artifact directories.
- Any repository text, scanner output, or sandbox log that goes into a prompt must be wrapped with `llm/injection_defense.wrap_untrusted`.
- Never add suppression comments (`nosec`, `nosemgrep`, `noqa: S`) to pass a check.
- Never mount the Docker socket into any container except the sandbox daemon.

## Code style
- Python 3.11+. Full type hints. `from __future__ import annotations` at the top of each module.
- Format and lint with Ruff. Type-check with mypy in strict mode for `patchpilot`, `sandbox_runner`, and `pp_contracts`.
- Raise domain exceptions from `errors.py`. Never raise bare `Exception` or leak stack traces to API clients.
- Use timezone-aware UTC datetimes and string UUIDs.
- Add a short docstring to every public class and function. No commented-out code.

## Testing
- Every implementation file needs its unit tests in the paths listed in the spec (Section 2.11).
- Run the tests for the file you changed before reporting done. Report the exact command and result.
- Do not weaken or delete a test to make it pass. If a test is wrong, say so and stop.
- Unit tests must not need Docker or the network. Use the fixtures in `backend/tests/conftest.py`.

## Working method
- Before writing code, state in two or three sentences what you will create and which spec entry you are following.
- At the end, list: files changed, tests run with results, and any assumptions you made.
- If the spec is ambiguous or a dependency file does not exist yet, stop and ask. Do not guess.
- Work in small steps. One file per task is the default.

## Models
- Use the model the human selects. Do not change it.
- Models must run locally or be explicitly approved for hosted use. Hosted providers stay disabled unless `ALLOW_HOSTED_LLM=true`.
- Do not use Llama models in configuration or code.