#!/usr/bin/env python3
"""
tools/ollama_diff_patcher.py
A robust Search/Replace block patcher for local models.
Asks Ollama to produce Aider-style SEARCH/REPLACE blocks,
and applies them with whitespace-tolerant matching.
Requires human unified diff acceptance before writing.
"""

from __future__ import annotations
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
import subprocess
import difflib
import os
import tempfile
import argparse

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "qwen2.5-coder:7b-instruct"

ACCEPTANCE_PHRASE = "ACCEPT DIFF"


def call_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }
    
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            return res_data.get("response", "")
    except urllib.error.URLError as e:
        print(f"[Ollama Diff Patcher] [ERROR] Failed to reach Ollama: {e}")
        sys.exit(1)


def parse_search_replace_blocks(response_text: str) -> list[tuple[str, str]]:
    """Parse Aider-style SEARCH/REPLACE blocks from the response."""
    blocks = []
    lines = response_text.splitlines()
    
    in_search = False
    in_replace = False
    
    search_lines = []
    replace_lines = []
    
    for line in lines:
        if "<<<<<<< SEARCH" in line:
            in_search = True
            in_replace = False
            search_lines = []
            continue
        elif "=======" in line and in_search:
            in_search = False
            in_replace = True
            replace_lines = []
            continue
        elif ">>>>>>> REPLACE" in line and in_replace:
            in_replace = False
            blocks.append(("\n".join(search_lines), "\n".join(replace_lines)))
            continue
            
        if in_search:
            search_lines.append(line)
        elif in_replace:
            replace_lines.append(line)
            
    return blocks


def normalize_lines(text: str) -> list[str]:
    """Normalize lines by stripping trailing whitespaces and ignoring empty lines."""
    return [line.rstrip() for line in text.splitlines()]


def find_exact_or_tolerant_match(file_content: str, search_block: str) -> tuple[int, int] | None:
    """
    Find starting and ending character index of search_block in file_content.
    Tolerates minor indentation/trailing whitespace mismatches.
    """
    # Try exact match first
    idx = file_content.find(search_block)
    if idx != -1:
        return idx, idx + len(search_block)
        
    # Tolerant line-by-line matching
    file_lines = file_content.splitlines()
    search_lines = search_block.splitlines()
    
    if not search_lines:
        return None
        
    num_search = len(search_lines)
    for i in range(len(file_lines) - num_search + 1):
        match = True
        for j in range(num_search):
            f_line = file_lines[i + j].strip()
            s_line = search_lines[j].strip()
            if f_line != s_line:
                match = False
                break
        if match:
            # Reconstruct character indices
            start_idx = len("\n".join(file_lines[:i])) + (1 if i > 0 else 0)
            end_idx = len("\n".join(file_lines[:i + num_search]))
            return start_idx, end_idx
            
    return None


def build_unified_diff(path: Path, before: str, after: str) -> str:
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)

    diff_lines = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=f"{path} (current)",
        tofile=f"{path} (proposed)",
        lineterm="",
    )

    return "".join(diff_lines)


def require_human_diff_acceptance(diff_text: str) -> bool:
    if not diff_text.strip():
        print("NO CHANGE: proposed output matches current file. Nothing to write.")
        return False

    print("\n" + "=" * 80)
    print("PROPOSED DIFF")
    print("=" * 80)
    print(diff_text)
    print("=" * 80)
    print("PATCHER_ACCEPTANCE_RULE step 7 requires explicit human acceptance.")
    print(f'Type exactly "{ACCEPTANCE_PHRASE}" to write this diff.')
    print("Anything else aborts without modifying files.")
    print("=" * 80)

    try:
        typed = input("> ")
    except EOFError:
        print("REJECTED: no interactive confirmation received. No files modified.")
        return False

    if typed == ACCEPTANCE_PHRASE:
        return True

    print("REJECTED: confirmation phrase did not match. No files modified.")
    return False


def atomic_write_text(path: Path, text: str) -> None:
    path = path.resolve()
    tmp_fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=str(path.parent),
        text=True,
    )

    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise


def main():
    parser = argparse.ArgumentParser(description="Ollama diff patcher")
    parser.add_argument("target", help="File to edit")
    parser.add_argument("instruction", help="Patch instruction")
    parser.add_argument("verify_command", nargs="?", default=None, help="Verification command")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the proposed diff but do not write any files.",
    )
    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.exists():
        print(f"[Ollama Diff Patcher] [ERROR] Target file does not exist: {target_path}")
        sys.exit(1)

    before_text = target_path.read_text(encoding="utf-8")

    prompt = f"""You are a precise coding assistant.
We want to modify the file: '{target_path.name}'
Here is the current content of the file:
---
{before_text}
---

Your task:
{args.instruction}

Provide your changes in one or more SEARCH/REPLACE blocks.
Format each block exactly like this:
<<<<<<< SEARCH
[exact lines to replace from the file]
=======
[new lines to insert]
>>>>>>> REPLACE

Output ONLY the SEARCH/REPLACE blocks. Do not include any explanation or introduction.
"""

    print(f"[Ollama Diff Patcher] Prompting local {DEFAULT_MODEL}...")
    response = call_ollama(prompt)
    blocks = parse_search_replace_blocks(response)
    
    if not blocks:
        print("[Ollama Diff Patcher] [ERROR] No SEARCH/REPLACE blocks found in response:")
        print(response)
        sys.exit(1)
        
    print(f"[Ollama Diff Patcher] Found {len(blocks)} patch block(s).")
    
    # Apply patches in memory
    after_text = before_text
    for idx, (search, replace) in enumerate(blocks):
        match = find_exact_or_tolerant_match(after_text, search)
        if not match:
            print(f"[Ollama Diff Patcher] [ERROR] Block {idx + 1} SEARCH failed to match file lines:")
            print(f"SEARCH BLOCK:\n{search}")
            sys.exit(1)
            
        start, end = match
        after_text = after_text[:start] + replace + after_text[end:]

    diff_text = build_unified_diff(target_path, before_text, after_text)

    if before_text == after_text:
        print("NO CHANGE: proposed output matches current file. Nothing to write.")
        sys.exit(0)

    if args.dry_run:
        print(diff_text)
        print("DRY RUN: no files modified.")
        sys.exit(0)

    if not require_human_diff_acceptance(diff_text):
        sys.exit(2)

    try:
        atomic_write_text(target_path, after_text)
        print(f"WROTE: {target_path}")

        # Verify syntax
        compiles = subprocess.run([sys.executable, "-m", "py_compile", str(target_path)], capture_output=True)
        if compiles.returncode != 0:
            raise RuntimeError(f"Syntax compilation failed:\n{compiles.stderr.decode()}")
            
        if args.verify_command:
            print(f"[Ollama Diff Patcher] Running validation: {args.verify_command}")
            verify_run = subprocess.run(args.verify_command, shell=True, capture_output=True)
            if verify_run.returncode != 0:
                raise RuntimeError(f"Verification command failed with code {verify_run.returncode}:\n{verify_run.stderr.decode()}")
                
        print(f"[Ollama Diff Patcher] [SUCCESS] Successfully patched {target_path}!")
        sys.exit(0)
        
    except Exception as e:
        print(f"[Ollama Diff Patcher] [FAILED] Verification failed. Rolling back changes: {e}")
        # Print generated blocks for debugging
        print("[Ollama Diff Patcher] Generated blocks were:")
        for idx, (search, replace) in enumerate(blocks):
            print(f"BLOCK {idx+1} SEARCH:\n{search}\nREPLACE:\n{replace}\n---")
        atomic_write_text(target_path, before_text)
        sys.exit(1)


if __name__ == "__main__":
    main()
