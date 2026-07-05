#!/usr/bin/env python3
"""
tools/ollama_patcher.py
A lightweight, fast alternative to Aider for local 7B models.
Calls Ollama's local HTTP API directly, receives code patches,
applies them, and runs verification checks.
"""

from __future__ import annotations
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
import subprocess

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "qwen2.5-coder:7b-instruct"

def call_ollama(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Send a direct prompt to local Ollama and return the text response."""
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
        print(f"[Ollama Patcher] [ERROR] Failed to reach Ollama at {OLLAMA_URL}: {e}")
        sys.exit(1)

def extract_code_block(response_text: str) -> str:
    """Extract code contents from a markdown code block."""
    lines = response_text.splitlines()
    code_lines = []
    in_block = False
    
    for line in lines:
        if line.strip().startswith("```"):
            in_block = not in_block
            continue
        if in_block:
            code_lines.append(line)
            
    if code_lines:
        return "\n".join(code_lines)
    return response_text # fallback if no code block markers found

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 tools/ollama_patcher.py <file_to_edit> <patch_instruction> [verify_command]")
        sys.exit(1)
        
    target_file = Path(sys.argv[1])
    instruction = sys.argv[2]
    verify_cmd = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not target_file.exists():
        print(f"[Ollama Patcher] [ERROR] Target file does not exist: {target_file}")
        sys.exit(1)
        
    print(f"[Ollama Patcher] Reading {target_file}...")
    file_content = target_file.read_text(encoding="utf-8")
    
    # Construct a highly focused prompt asking Ollama to output ONLY the updated code
    prompt = f"""You are a precise coding assistant.
We want to modify the file: '{target_file.name}'
Here is the current content of the file:
---
{file_content}
---

Your task:
{instruction}

Provide the ENTIRE updated content of the file. Output ONLY the updated file contents inside a single code block starting with ```python (or the appropriate language block) and ending with ```. Do not include any explanation or introduction.
"""

    print(f"[Ollama Patcher] Prompting local {DEFAULT_MODEL}...")
    response = call_ollama(prompt)
    updated_code = extract_code_block(response)
    
    if not updated_code or updated_code.strip() == file_content.strip():
        print("[Ollama Patcher] No changes or empty response generated.")
        sys.exit(1)
        
    # Write updated code
    print(f"[Ollama Patcher] Applying changes to {target_file}...")
    backup_file = target_file.with_suffix(target_file.suffix + ".bak")
    target_file.rename(backup_file) # Keep backup in case verification fails
    
    try:
        target_file.write_text(updated_code, encoding="utf-8")
        
        # Verify syntax and tests
        compiles = subprocess.run([sys.executable, "-m", "py_compile", str(target_file)], capture_output=True)
        if compiles.returncode != 0:
            raise RuntimeError(f"Syntax compilation failed:\n{compiles.stderr.decode()}")
            
        if verify_cmd:
            print(f"[Ollama Patcher] Running validation: {verify_cmd}")
            verify_run = subprocess.run(verify_cmd, shell=True, capture_output=True)
            if verify_run.returncode != 0:
                raise RuntimeError(f"Verification command failed with code {verify_run.returncode}:\n{verify_run.stderr.decode()}")
                
        # Clean up backup on success
        backup_file.unlink()
        print(f"[Ollama Patcher] [SUCCESS] Successfully patched {target_file}!")
        
    except Exception as e:
        print(f"[Ollama Patcher] [FAILED] Verification failed. Rolling back changes: {e}")
        if target_file.exists():
            target_file.unlink()
        backup_file.rename(target_file)
        sys.exit(1)

if __name__ == "__main__":
    main()
