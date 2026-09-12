#!/usr/bin/env python3
"""Codex lifecycle adapter; the original Claude hooks remain the policy source."""

import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

ROLES = {"builder", "implementer", "test-runner", "verifier", "code-reviewer",
         "docs-writer", "security-auditor"}
SCRIPTS = {"PreToolUse": "guard-git-destructive.sh", "SubagentStop": "audit-subagent.sh",
           "Stop": "loop-guard.sh", "PreCompact": "precompact-checkpoint.sh"}


def root_at(cwd):
    result = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--show-toplevel"],
                            capture_output=True, text=True, check=True)
    return Path(result.stdout.strip()).resolve()


def state_path(root):
    return root / "loop/.codex-session.json"


def read_state(root):
    path = state_path(root)
    state = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(state, dict):
        raise ValueError("loop/.codex-session.json must contain an object")
    return state


def save_state(root, state):
    path = state_path(root)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as stream:
        temp = Path(stream.name)
        json.dump(state, stream)
        stream.write("\n")
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def deny(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
            "permissionDecision": "deny", "permissionDecisionReason": reason}}


def command_text(payload):
    value = payload.get("tool_input") or {}
    if not isinstance(value, dict):
        raise ValueError("tool_input must be an object")
    command = value.get("command", value.get("cmd"))
    if isinstance(command, list) and all(isinstance(part, str) for part in command):
        # The shell tool may send ["bash", "-lc", "..."] instead of unified exec's cmd.
        if len(command) >= 3 and command[-2] in ("-c", "-lc", "-ic"):
            command = command[-1]
        else:
            command = shlex.join(command)
    if not isinstance(command, str) or not command.strip():
        raise ValueError("shell hook has no readable command")
    return command


def control_action(root, command, cwd):
    """Recognize only a standalone invocation of this installed script."""
    argv = shlex.split(command)
    if len(argv) != 3 or Path(argv[0]).name not in ("python3", "python"):
        return None
    script = Path(argv[1])
    if not script.is_absolute():
        script = Path(cwd) / script
    if script.resolve() != root / ".codex/hooks/loop.py":
        return None
    return argv[2] if argv[2] in ("activate", "deactivate", "doctor") else None


def run_original(root, event, payload):
    script = root / ".claude/hooks" / SCRIPTS[event]
    result = subprocess.run(["sh", str(script)], input=json.dumps(payload),
                            capture_output=True, text=True, cwd=root, timeout=20)
    if result.returncode:
        raise RuntimeError(f"{script.name} exited {result.returncode}: {result.stderr.strip()}")
    value = json.loads(result.stdout) if result.stdout.strip() else {}
    if not isinstance(value, dict):
        raise ValueError(f"{script.name} did not return a JSON object")
    return value


def dispatch(payload):
    if not isinstance(payload, dict):
        raise ValueError("hook payload must be an object")
    event = payload.get("hook_event_name")
    if event not in SCRIPTS:
        return {}
    root = root_at(payload["cwd"])
    normalized = dict(payload, cwd=str(root))
    if event == "PreToolUse":
        command = command_text(payload)
        normalized["tool_input"] = {"command": command}
        decision = run_original(root, event, normalized)
        if decision:
            return decision
        action = control_action(root, command, payload["cwd"])
        if action:
            if not (root / "loop").is_dir():
                return deny("Run $loop-init before activating the loop.")
            session = payload.get("session_id")
            transcript = payload.get("transcript_path")
            if not session or not transcript:
                return deny("Codex did not supply session and transcript identity; cannot scope loop hooks.")
            state = read_state(root)
            if action == "activate":
                if state.get("active") and state.get("session_id") != session:
                    return deny("Another Codex loop session is active. Stop it and explicitly release loop/.codex-session.json before resuming here.")
                state = {"active": True, "session_id": session, "transcript_path": transcript}
            elif action == "deactivate":
                if state.get("active") and state.get("session_id") != session:
                    return deny("Only the owning session may deactivate this loop.")
                state["active"] = False
            state["last_control"] = {"action": action, "session_id": session}
            save_state(root, state)
        return {}
    if not (root / "loop").is_dir():
        return {}
    if event == "SubagentStop":
        if payload.get("agent_type") not in ROLES:
            return {}
        normalized["last_assistant_message"] = payload.get("last_assistant_message") or ""
        before = root / "loop/AUDIT.log"
        old_size = before.stat().st_size if before.exists() else 0
        result = run_original(root, event, normalized)
        if not before.exists() or before.stat().st_size <= old_size:
            raise RuntimeError("audit hook did not append a record")
        return result
    state = read_state(root)
    # Compare both identities: child hook events can carry the parent's session id.
    if not state.get("active") or not payload.get("transcript_path"):
        return {}
    if any(state.get(key) != payload.get(key) for key in ("session_id", "transcript_path")):
        return {}
    return run_original(root, event, normalized)


def main():
    if len(sys.argv) == 2 and sys.argv[1] in ("activate", "deactivate", "doctor"):
        root = root_at(Path.cwd())
        state = read_state(root)
        receipt = state.get("last_control", {})
        session = os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SESSION_ID")
        if not session or receipt != {"action": sys.argv[1], "session_id": session}:
            sys.exit("Loop hook activation not confirmed. Review/trust project hooks in /hooks, then retry this standalone command inside Codex.")
        # Consume the receipt: disabling hooks after one successful call must not
        # make a later doctor/activate appear to have passed a fresh lifecycle check.
        state.pop("last_control", None)
        save_state(root, state)
        print(f"Loop hooks confirmed: {sys.argv[1]} (session {session}).")
        return
    payload = {}
    try:
        payload = json.load(sys.stdin)
        result = dispatch(payload)
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        reason = f"Loop hook failed: {error}"
        # An unreadable shell check must not silently permit a destructive command.
        if not isinstance(payload, dict) or payload.get("hook_event_name") in (None, "PreToolUse"):
            result = deny(reason)
        else:
            result = {"systemMessage": reason}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
