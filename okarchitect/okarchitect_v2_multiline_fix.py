#!/usr/bin/env python3
"""
OKArchitect v2 - Session Memory + Interactive Control
Based on OKGPT architecture, optimized for ZW/AP/EngAIn workflows

NEW FEATURES:
- Persistent session memory across rounds
- Interactive menu after each consultation
- Options: continue, guide, pause, end
- Save/resume sessions
"""

import requests
import json
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import time
import os
from datetime import datetime

@dataclass
class ArchitectMember:
    """A member of the OKArchitect council"""
    name: str
    model: str
    specialty: str
    personality: str
    
    def __repr__(self):
        return f"{self.name} ({self.specialty})"

@dataclass
class SessionMessage:
    """A single message in the session history"""
    role: str  # 'user', 'user_guidance', or member name
    content: str
    timestamp: float = field(default_factory=time.time)
    round_number: int = 0

class SessionManager:
    """Manages persistent session memory"""
    
    def __init__(self, session_dir: str = None):
        if session_dir is None:
            session_dir = os.path.expanduser("~/Downloads/EngAIn/okarchitect/sessions")
        
        self.session_dir = session_dir
        os.makedirs(session_dir, exist_ok=True)
        
        self.session_id = f"session_{int(time.time())}"
        self.round_number = 0
        self.messages: List[SessionMessage] = []
        self.active = True
    
    def add_message(self, role: str, content: str):
        """Add a message to session history"""
        msg = SessionMessage(
            role=role,
            content=content,
            round_number=self.round_number
        )
        self.messages.append(msg)
    
    def get_history_for_prompt(self) -> str:
        """Format history for LLM prompt"""
        if not self.messages:
            return ""
        
        history = "\n=== SESSION HISTORY ===\n\n"
        for msg in self.messages:
            history += f"[Round {msg.round_number}] {msg.role}:\n{msg.content}\n\n"
        history += "=== END HISTORY ===\n\n"
        return history
    
    def save_session(self) -> str:
        """Save session to disk, return filepath"""
        filepath = os.path.join(self.session_dir, f"{self.session_id}.json")
        
        data = {
            "session_id": self.session_id,
            "round_number": self.round_number,
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp,
                    "round_number": msg.round_number
                }
                for msg in self.messages
            ],
            "saved_at": time.time()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    @classmethod
    def load_session(cls, session_id: str, session_dir: str = None) -> 'SessionManager':
        """Load a saved session"""
        if session_dir is None:
            session_dir = os.path.expanduser("~/Downloads/EngAIn/okarchitect/sessions")
        
        filepath = os.path.join(session_dir, f"{session_id}.json")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Session not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        manager = cls(session_dir)
        manager.session_id = data["session_id"]
        manager.round_number = data["round_number"]
        manager.messages = [
            SessionMessage(
                role=msg["role"],
                content=msg["content"],
                timestamp=msg["timestamp"],
                round_number=msg["round_number"]
            )
            for msg in data["messages"]
        ]
        
        return manager

class OKArchitect:
    def __init__(self, base_url: str = "http://localhost:11434/api/generate", 
                 project_brief_path: Optional[str] = None,
                 session_manager: Optional[SessionManager] = None):
        """Initialize OKArchitect council with EngAIn project context"""
        
        # Ollama configuration
        self.base_url = base_url
        self.backup_model = "phi3:latest"
        
        # Session management
        self.session = session_manager or SessionManager()
        
        # Load project brief FIRST
        self.project_brief = self._load_project_brief(project_brief_path)
        
        # Define members with BASE personalities (brief added at call time)
        self.members = {
            "Reasoner": ArchitectMember(
                name="Reasoner",
                model="dolphin-llama3:latest",
                specialty="Strategic Architecture",
                personality="You are the big-picture strategic architect. You think about overall system design, architectural decisions, and high-level patterns. You understand trade-offs and guide the team toward coherent solutions."
            ),
            "Validator": ArchitectMember(
                name="Validator",
                model="phi3:mini-128k",
                specialty="Fast Validation",
                personality="You are the fast validator. You catch errors quickly, perform sanity checks, and prevent runaway logic. You're the safety net that keeps the council honest and grounded."
            ),
            "EngineerA": ArchitectMember(
                name="EngineerA",
                model="deepseek-coder:6.7b",
                specialty="Systems Engineering",
                personality="You are the main systems engineer. You focus on practical implementation, Python correctness, and making things work in real code. You're the backbone of implementation."
            ),
            "EngineerB": ArchitectMember(
                name="EngineerB",
                model="qwen2.5-coder:7b",
                specialty="Formal Code Patterns",
                personality="You are the formal patterns specialist. You write strict, clean code with low error rates. You enforce type safety, immutability, and structural correctness."
            ),
            "StructuralLogic": ArchitectMember(
                name="StructuralLogic",
                model="joreilly86/structural_llama_3.0",
                specialty="Mathematical Logic",
                personality="You are the mathematical and structural logic specialist. You excel at algorithms, optimization, physics calculations, and formal logic systems."
            )
        }
        
        # Council order (for sequential consultation)
        self.council = [
            self.members["Reasoner"],
            self.members["Validator"],
            self.members["EngineerA"],
            self.members["EngineerB"],
            self.members["StructuralLogic"]
        ]
        
        print(f"✅ OKArchitect initialized with {len(self.council)} members")
        if self.project_brief:
            print(f"✅ EngAIn project context loaded ({len(self.project_brief)} chars)")
        print(f"📋 Session ID: {self.session.session_id}")
    
    def _load_project_brief(self, path=None):
        """Load EngAIn project brief as plain text context."""
        if path is None:
            # Load the code reference with working examples
            path = os.path.expanduser("~/Downloads/EngAIn/engain_code_reference.txt")
    
        if not os.path.exists(path):
            print(f"⚠️  Project brief not found: {path}")
            return ""
    
        # Read the full brief
        with open(path, 'r') as f:
            brief = f.read()
    
        return brief
    
    def _call_ollama(self, model: str, prompt: str, timeout: int = 90) -> Optional[str]:
        """Call Ollama API with timeout handling"""
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 2000
                }
            }
            
            response = requests.post(
                self.base_url,
                json=payload,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                print(f"⚠️  API error: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout after {timeout}s")
            return None
        except Exception as e:
            print(f"❌ Error calling model: {e}")
            return None
    
    def consult_member(self, member: ArchitectMember, prompt: str, 
                      context: Optional[str] = None, timeout: int = 90) -> str:
        """Consult a single council member"""
        
        # Start with base personality
        full_prompt = f"{member.specialty}: {member.personality}\n\n"
        
        # Add session history
        history = self.session.get_history_for_prompt()
        if history:
            full_prompt += history
        
        # Add immediate context (from previous members in THIS round)
        if context:
            full_prompt += f"Previous responses in this round:\n{context}\n\n"
        
        # CRITICAL: Add project brief RIGHT BEFORE question (recency bias)
        if self.project_brief:
            full_prompt += (
                "\n" + "="*60 + "\n"
                "CRITICAL: READ THIS REFERENCE BEFORE ANSWERING\n"
                + "="*60 + "\n"
                f"{self.project_brief}\n"
                + "="*60 + "\n"
                "When answering, REFERENCE the code examples above.\n"
                "If the brief already lists a subsystem, DO NOT suggest it again.\n"
                + "="*60 + "\n\n"
            )
        
        # Add the actual question
        full_prompt += f"Question: {prompt}\n\nYour response:"
        
        print(f"🤔 {member.name} is thinking...")
        
        # Try primary model
        response = self._call_ollama(member.model, full_prompt, timeout)
        
        # Fallback to backup if needed
        if response is None:
            print(f"⚠️  Falling back to {self.backup_model}...")
            response = self._call_ollama(self.backup_model, full_prompt, timeout=60)
        
        if response is None:
            response = f"[{member.name} timed out or failed]"
        
        return response
    
    def consultation_round(self, prompt: str, is_initial: bool = True) -> Dict[str, str]:
        """Run one round of consultation with all members"""
        
        if is_initial:
            self.session.round_number += 1
            print(f"\n{'='*60}")
            print(f"🏗️  ROUND {self.session.round_number}: Initial Consultation")
            print(f"{'='*60}\n")
            
            # Add user question to session
            self.session.add_message("user", prompt)
        else:
            self.session.round_number += 1
            print(f"\n{'='*60}")
            print(f"🏗️  ROUND {self.session.round_number}: Council Refinement")
            print(f"{'='*60}\n")
        
        responses = {}
        context = ""
        
        for member in self.council:
            # Each member sees history + this round's context
            response = self.consult_member(member, prompt, context)
            responses[member.name] = response
            
            # Add to session
            self.session.add_message(member.name, response)
            
            # Display response
            print(f"\n🗣️  **{member.name}** ({member.specialty}):")
            print(f"{response}")
            print("-" * 60)
            
            # Build context for next member in THIS round
            context += f"\n{member.name}: {response}\n"
        
        return responses
    
    def show_menu(self) -> str:
        """Show interactive menu and get user choice"""
        print(f"\n{'='*60}")
        print("📋 What's next?")
        print(f"{'='*60}")
        print("1. Continue council (they refine based on full history)")
        print("2. Add guidance, then continue (you steer next iteration)")
        print("3. Pause session (save and exit, resume later)")
        print("4. End session (clear memory, finish)")
        print(f"{'='*60}")
        
        while True:
            choice = input("Choice [1-4]: ").strip()
            if choice in ['1', '2', '3', '4']:
                return choice
            print("Invalid choice. Enter 1, 2, 3, or 4.")
    
    def interactive_session(self, initial_question: str):
        """Run an interactive multi-round session"""
        
        # Initial round
        self.consultation_round(initial_question, is_initial=True)
        
        # Interactive loop
        while self.session.active:
            choice = self.show_menu()
            
            if choice == '1':
                # Continue without user input
                refinement_prompt = (
                    f"Round {self.session.round_number + 1}: Based on the full discussion history, "
                    "refine your response. Address gaps, improve specifics, correct errors, "
                    "and reference other members' points."
                )
                self.consultation_round(refinement_prompt, is_initial=False)
            
            elif choice == '2':
                # User provides guidance
                print(f"\n{'='*60}")
                print("💬 Your Guidance (or correction):")
                print("(Paste your message, then type 'END' on a new line, or Ctrl+D)")
                print(f"{'='*60}")
                
                # Collect multi-line input
                lines = []
                print(">>> ", end="", flush=True)
                try:
                    while True:
                        line = input()
                        if line.strip() == "END":
                            break
                        lines.append(line)
                except EOFError:
                    pass  # Ctrl+D pressed
                
                user_input = "\n".join(lines).strip()
                
                if not user_input:
                    print("No input provided.")
                    continue
                
                # Add guidance to session
                self.session.add_message("user_guidance", user_input)
                
                # Council responds to guidance
                guidance_prompt = f"Respond to this guidance from the user: {user_input}"
                self.consultation_round(guidance_prompt, is_initial=False)
            
            elif choice == '3':
                # Pause and save
                filepath = self.session.save_session()
                print(f"\n{'='*60}")
                print("💾 Session Paused")
                print(f"{'='*60}")
                print(f"📁 Saved to: {filepath}")
                print(f"📊 Rounds completed: {self.session.round_number}")
                print(f"💬 Messages in history: {len(self.session.messages)}")
                print(f"\nTo resume: ./okarchitect.py --resume {self.session.session_id}")
                print(f"{'='*60}\n")
                self.session.active = False
                break
            
            elif choice == '4':
                # End session
                print(f"\n{'='*60}")
                print("🏁 Session Ended")
                print(f"{'='*60}")
                print(f"📊 Rounds completed: {self.session.round_number}")
                print(f"💬 Total messages: {len(self.session.messages)}")
                print(f"{'='*60}\n")
                self.session.active = False
                break
    
    def interactive_mode(self):
        """Interactive CLI for the OKArchitect council"""
        print("\n" + "=" * 60)
        print("🏗️  OKArchitect v2 - Session Memory + Interactive Control")
        print("    For EngAIn, ZW, AP Rules, and Game Architecture")
        print("=" * 60)
        print("\nCouncil Members:")
        for member in self.council:
            print(f"  • {member.name}: {member.specialty}")
        print("\nCommands:")
        print("  consult [question]  - Start session-based consultation")
        print("  ask [name] [q]      - Quick ask (no session)")
        print("  sessions            - List saved sessions")
        print("  help                - Show this help")
        print("  exit                - Quit OKArchitect")
        print("=" * 60)
        
        while True:
            try:
                user_input = input("\n🏗️  OKArchitect> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 OKArchitect session ended.")
                    break
                
                elif user_input.lower() == 'help':
                    print("\nCommands:")
                    print("  consult [question]  - Start multi-round session with memory")
                    print("  ask [name] [q]      - Quick single question (no history)")
                    print("  sessions            - List saved sessions")
                    
                elif user_input.lower().startswith('consult '):
                    question = user_input[8:].strip()
                    if question:
                        # Start new session
                        self.session = SessionManager()
                        self.interactive_session(question)
                    else:
                        print("Usage: consult [question]")
                    
                elif user_input.lower().startswith('ask '):
                    parts = user_input[4:].split(maxsplit=1)
                    if len(parts) < 2:
                        print("Usage: ask [member_name] [question]")
                        continue
                    
                    member_name = parts[0].capitalize()
                    question = parts[1]
                    
                    # Find the member
                    member = next((m for m in self.council if m.name.lower() == member_name.lower()), None)
                    if member:
                        response = self.consult_member(member, question)
                        print(f"\n🗣️  **{member.name}**: {response}")
                    else:
                        print(f"Unknown member: {member_name}")
                        print(f"Available: {', '.join(m.name for m in self.council)}")
                
                elif user_input.lower() == 'sessions':
                    session_dir = os.path.expanduser("~/Downloads/EngAIn/okarchitect/sessions")
                    if not os.path.exists(session_dir):
                        print("No saved sessions yet.")
                        continue
                    
                    files = [f for f in os.listdir(session_dir) if f.endswith('.json')]
                    if not files:
                        print("No saved sessions yet.")
                    else:
                        print(f"\n📁 Saved Sessions ({len(files)}):")
                        for f in sorted(files, reverse=True):
                            session_id = f.replace('.json', '')
                            filepath = os.path.join(session_dir, f)
                            mtime = os.path.getmtime(filepath)
                            date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
                            print(f"  • {session_id} (saved {date_str})")
                        print(f"\nTo resume: ./okarchitect.py --resume [session_id]")
                
                else:
                    # Treat as implicit consult
                    self.session = SessionManager()
                    self.interactive_session(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n👋 OKArchitect session interrupted.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()


def main():
    """Main entry point for OKArchitect"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OKArchitect v2 - Session Memory + Interactive Control")
    parser.add_argument('--url', default='http://localhost:11434/api/generate',
                       help='Ollama API URL')
    parser.add_argument('--quick', '-q', metavar='QUESTION',
                       help='Quick consultation (non-interactive, no session)')
    parser.add_argument('--resume', '-r', metavar='SESSION_ID',
                       help='Resume a saved session')
    
    args = parser.parse_args()
    
    # Handle resume
    if args.resume:
        try:
            session = SessionManager.load_session(args.resume)
            print(f"✅ Resumed session: {args.resume}")
            print(f"📊 Rounds so far: {session.round_number}")
            print(f"💬 Messages: {len(session.messages)}")
            
            architect = OKArchitect(base_url=args.url, session_manager=session)
            
            # Continue from where we left off
            refinement_prompt = (
                f"Continuing from Round {session.round_number}. "
                "Review the full history and provide your next response."
            )
            architect.interactive_session(refinement_prompt)
            
        except FileNotFoundError as e:
            print(f"❌ {e}")
            return
    
    # Handle quick mode
    elif args.quick:
        architect = OKArchitect(base_url=args.url)
        architect.consultation_round(args.quick, is_initial=True)
    
    # Interactive mode
    else:
        architect = OKArchitect(base_url=args.url)
        architect.interactive_mode()


if __name__ == "__main__":
    main()
