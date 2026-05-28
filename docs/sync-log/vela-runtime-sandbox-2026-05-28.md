# VELA runtime sandbox verification - 2026-05-28

## Scope

Verified the VELA-owned core runtime install without touching the user's real runtime homes.

## Sandbox Targets

- `CODEX_HOME=<VELA_WORKSPACE_TMP>/vela-runtime-sandbox/codex`
- `VELA_HOME=<VELA_WORKSPACE_TMP>/vela-runtime-sandbox/vela`

The real user runtime directories were not used as install targets.

## Result

`vela local-env install-runtime --include core,automation,toolchain --commit` installed:

- 16 public research skills.
- The local research stack payload under the sandbox `VELA_HOME`.
- `envctl` Windows and POSIX shims.
- Runtime install receipts.

After installation, `vela local-env doctor-runtime --include core,automation,toolchain --strict` returned `ok=true` and `ready=true`.

## Additional Fix

The CodeGraph status probe now resolves Windows `.cmd` and `.bat` shims before executing `codegraph status --json <project>`. This prevents a false `command-not-found` style result when CodeGraph is installed through an npm-style command shim.

## Boundary

`doctor-runtime --include all --strict` still requires user-local MCP config sections and Codex plugin cache state. VELA must not synthesize those from another user's machine. Core/runtime readiness and optional user-runtime readiness remain separate checks.
