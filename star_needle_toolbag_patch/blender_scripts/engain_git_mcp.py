# filename: mcp_servers/engain_git_mcp.py
from __future__ import annotations

import json
import logging
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from subprocess import CompletedProcess, run
from typing import Any, Dict, List, Optional

from mcp.server.fastmcp import FastMCP

# IMPORTANT (stdio): never write to stdout; stdout is reserved for JSON-RPC. :contentReference[oaicite:3]{index=3}
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("engain_git_mcp")

mcp = FastMCP("EngAIn Git MCP", json_response=True)


@dataclass(frozen=True)
class GitConfig:
    repo_root: Path
    max_output_chars: int


def _load_cfg() -> GitConfig:
    root = os.environ.get("ENGAIN_REPO_ROOT", os.getcwd())
    repo_root = Path(root).expanduser().resolve()
    max_output_chars = int(os.environ.get("ENGAIN_GIT_MAX_OUTPUT_CHARS", "200000"))  # 200k chars
    return GitConfig(repo_root=repo_root, max_output_chars=max_output_chars)


CFG = _load_cfg()


def _cap(s: str) -> Dict[str, Any]:
    if len(s) <= CFG.max_output_chars:
        return {"text": s, "truncated": False, "max_output_chars": CFG.max_output_chars}
    return {"text": s[: CFG.max_output_chars], "truncated": True, "max_output_chars": CFG.max_output_chars}


def _is_git_repo(root: Path) -> bool:
    return (root / ".git").exists()


def _safe_timeout(timeout_s: float) -> float:
    try:
        t = float(timeout_s)
    except Exception:
        return 12.0
    if t < 0.1:
        return 0.1
    if t > 60.0:
        return 60.0
    return t


def _git(args: List[str], timeout_s: float = 12.0) -> Dict[str, Any]:
    if not _is_git_repo(CFG.repo_root):
        return {"ok": False, "error": "not_a_git_repo", "repo_root": str(CFG.repo_root)}

    cmd = ["git", "-C", str(CFG.repo_root), *args]
    try:
        proc: CompletedProcess[str] = run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=_safe_timeout(timeout_s),
        )
        out = (proc.stdout or "")
        err = (proc.stderr or "")
        payload: Dict[str, Any] = {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "cmd": cmd,
            "stdout": _cap(out),
            "stderr": _cap(err),
        }
        return payload
    except Exception as e:
        return {"ok": False, "error": "exception", "detail": str(e), "cmd": cmd}


@mcp.tool()
def git_status(porcelain: bool = True, timeout_s: float = 12.0) -> Dict[str, Any]:
    """Read-only status."""
    args = ["status"]
    if porcelain:
        args += ["--porcelain=v1", "--untracked-files=all"]
    return _git(args, timeout_s)


@mcp.tool()
def git_diff(staged: bool = False, paths: Optional[List[str]] = None, timeout_s: float = 20.0) -> Dict[str, Any]:
    """Read-only diff (optionally staged) with optional path filtering."""
    args = ["diff"]
    if staged:
        args.append("--cached")
    args += ["--no-color"]
    if paths:
        args.append("--")
        args.extend([p for p in paths if isinstance(p, str) and p.strip()])
    return _git(args, timeout_s)


@mcp.tool()
def git_log(limit: int = 20, path: Optional[str] = None, timeout_s: float = 12.0) -> Dict[str, Any]:
    """Read-only log with a sane format."""
    try:
        n = int(limit)
    except Exception:
        n = 20
    if n < 1:
        n = 1
    if n > 200:
        n = 200

    args = ["log", f"-n{n}", "--date=iso-strict", "--pretty=format:%H%n%ad%n%an%n%s%n----"]
    if path and isinstance(path, str) and path.strip():
        args += ["--", path.strip()]
    return _git(args, timeout_s)


@mcp.tool()
def git_show(ref: str, timeout_s: float = 12.0) -> Dict[str, Any]:
    """Read-only show for a commit/tag/blob ref."""
    if not isinstance(ref, str) or not ref.strip():
        return {"ok": False, "error": "empty_ref"}
    return _git(["show", "--no-color", ref.strip()], timeout_s)


@mcp.tool()
def git_grep(pattern: str, timeout_s: float = 20.0) -> Dict[str, Any]:
    """Read-only grep (fast search across tracked + working tree)."""
    if not isinstance(pattern, str) or not pattern.strip():
        return {"ok": False, "error": "empty_pattern"}
    # -n line numbers, -I ignore binary, --full-name paths, --no-color for clean output
    return _git(["grep", "-n", "-I", "--full-name", "--no-color", pattern], timeout_s)


@mcp.resource("engain-git://config")
def git_config_resource() -> str:
    return json.dumps(
        {
            "repo_root": str(CFG.repo_root),
            "max_output_chars": CFG.max_output_chars,
            "is_git_repo": _is_git_repo(CFG.repo_root),
        },
        indent=2,
        ensure_ascii=False,
    )


@mcp.prompt()
def engain_git_usage() -> str:
    return (
        "You have read-only Git tools.\n"
        "Use git_status() to see what changed.\n"
        "Use git_diff(staged=False) to inspect changes.\n"
        "Use git_log() for history and git_grep() to find symbols/strings.\n"
        "Do not ask to commit or modify; this server is inspection-only."
    )


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").strip()
    mcp.run(transport=transport)
