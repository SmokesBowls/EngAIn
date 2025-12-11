#!/usr/bin/env python3
"""
OKArchitect - Specialized AI Council for EngAIn Development
Based on OKGPT architecture, optimized for ZW/AP/EngAIn workflows

Council Members:
- Reasoner: Dolphin-Llama3 (big-picture thinking, architectural decisions)
- Validator: Phi3-Mini (fast validation, timeout prevention, sanity checks)
- EngineerA: DeepSeek-Coder 6.7b (main engineer - Python, systems, broad correctness)
- EngineerB: Qwen2.5-Coder 7b (strict patterns, low hallucination, formal code)
- StructuralLogic: Structural-Llama 3.0 (math, physics, AP rules, ZW transforms)
"""

import requests
import json
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass
import time
import os

@dataclass
class ArchitectMember:
    """A member of the OKArchitect council"""
    name: str
    model: str
    specialty: str
    personality: str
    
    def __repr__(self):
        return f"{self.name} ({self.specialty})"

class OKArchitect:
    def __init__(self, base_url: str = "http://localhost:11434/api/generate", 
                 project_brief_path: Optional[str] = None):
        """Initialize OKArchitect council with EngAIn project context"""
        
        # Ollama configuration
        self.base_url = base_url
        self.backup_model = "phi3:latest"
        
        # Conversation tracking
        self.conversation_history = []
        
        # Load project brief FIRST
        self.project_brief = self._load_project_brief(project_brief_path)
        
        # Define members WITH project context injected
        self.members = {
            "Reasoner": ArchitectMember(
                name="Reasoner",
                model="dolphin-llama3:latest",
                specialty="Strategic Architecture",
                personality=self._with_context(
                    "You are the strategic architect. You analyze problems from a high level, "
                    "identify patterns, and suggest architectural approaches. You think about "
                    "maintainability, scalability, and design principles."
                )
            ),
            "Validator": ArchitectMember(
                name="Validator",
                model="phi3:mini-128k",
                specialty="Fast Validation",
                personality=self._with_context(
                    "You are the quick validator. You catch obvious errors, perform sanity checks, "
                    "and identify edge cases rapidly. You prevent runaway logic and validate assumptions."
                )
            ),
            "EngineerA": ArchitectMember(
                name="EngineerA",
                model="deepseek-coder:6.7b",
                specialty="Systems Engineering",
                personality=self._with_context(
                    "You are the main systems engineer. You write clean, correct Python code. "
                    "You focus on practical implementation, error handling, and robust patterns."
                )
            ),
            "EngineerB": ArchitectMember(
                name="EngineerB",
                model="qwen2.5-coder:7b",
                specialty="Formal Code Patterns",
                personality=self._with_context(
                    "You are the formal patterns specialist. You write strict, clean code with "
                    "low error rates. You enforce type safety, immutability, and structural correctness."
                )
            ),
            "StructuralLogic": ArchitectMember(
                name="StructuralLogic",
                model="joreilly86/structural_llama_3.0",
                specialty="Mathematical Logic",
                personality=self._with_context(
                    "You are the mathematical and structural logic specialist. You excel at "
                    "algorithms, optimization, physics calculations, and formal logic systems."
                )
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
            print(f"✅ EngAIn project context loaded")
        
        # ... rest of init ...
    
    def _load_project_brief(self, path=None):
        """Load EngAIn project brief as plain text context."""
        if path is None:
            # Load the code reference with working examples
            path = os.path.expanduser("~/Downloads/EngAIn/engain_code_reference.txt")
    
        if not os.path.exists(path):
            print(f"⚠️  Project brief not found: {path}")
            return ""
    
        # Just read the text - no parsing needed!
        with open(path, 'r') as f:
            brief = f.read()
    
        print(f"✅ Loaded EngAIn project brief ({len(brief)} chars)")
        return brief
    
    def _with_context(self, base_personality: str) -> str:
        """Inject project brief into member personality."""
        if not self.project_brief:
            return base_personality
    
        # Just prepend the brief as text
        return (
            "# EngAIn Project Context\n\n"
            f"{self.project_brief}\n\n"
            "---\n\n"
            f"{base_personality}\n\n"
            "When answering, reference the EngAIn subsystems and follow the 3-layer pattern."
        )
        
    def consult_member(self, member: ArchitectMember, prompt: str, 
                      context: Optional[str] = None, timeout: int = 90) -> str:
        """
        Consult a single council member with optional context from previous responses
        """
        # Build the full prompt with personality and context
        full_prompt = f"You are {member.name}, {member.specialty}.\n\n"
        full_prompt += f"Your approach: {member.personality}\n\n"
        
        if context:
            full_prompt += f"Context from other council members:\n{context}\n\n"
        
        full_prompt += f"Question: {prompt}\n\n"
        full_prompt += "Provide your perspective based on your specialty:"
        
        payload = {
            "model": member.model,
            "prompt": full_prompt,
            "stream": False
        }
        
        try:
            print(f"🤔 {member.name} is thinking...")
            response = requests.post(self.base_url, json=payload, timeout=timeout)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response generated")
            elif response.status_code == 404:
                print(f"⚠️  Model {member.model} not found. Trying backup...")
                return self._try_backup(full_prompt, timeout)
            else:
                return f"Error: HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            print(f"⏱️  {member.name} timed out. Trying backup...")
            return self._try_backup(full_prompt, timeout // 2)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _try_backup(self, prompt: str, timeout: int) -> str:
        """Fallback to backup model on timeout or error"""
        try:
            payload = {
                "model": self.backup_model,
                "prompt": prompt,
                "stream": False
            }
            response = requests.post(self.base_url, json=payload, timeout=timeout)
            if response.status_code == 200:
                result = response.json()
                return f"[Backup response] {result.get('response', 'No response')}"
            else:
                return f"Backup also failed: HTTP {response.status_code}"
        except Exception as e:
            return f"Backup failed: {str(e)}"
    
    def consult_council(self, prompt: str, sequential: bool = True) -> Dict[str, str]:
        """
        Consult the full council on a question
        
        Args:
            prompt: The question or problem to discuss
            sequential: If True, each member sees previous responses (recommended)
                       If False, all members respond independently
        
        Returns:
            Dictionary mapping member names to their responses
        """
        print(f"\n🏗️  Consulting OKArchitect Council: {prompt}\n")
        print("=" * 60)
        
        responses = {}
        context = ""
        
        for member in self.council:
            # In sequential mode, each member sees what came before
            member_context = context if sequential else None
            
            response = self.consult_member(member, prompt, member_context)
            responses[member.name] = response
            
            # Display response
            print(f"\n🗣️  **{member.name}** ({member.specialty}):")
            print(f"{response}")
            print("-" * 60)
            
            # Build context for next member (in sequential mode)
            if sequential:
                context += f"\n{member.name}: {response}\n"
        
        # Save to history
        self.conversation_history.append({
            "prompt": prompt,
            "responses": responses,
            "timestamp": time.time()
        })
        
        return responses
    
    def debate_mode(self, prompt: str, rounds: int = 2) -> List[Dict[str, str]]:
        """
        Enable multi-round debate where members respond to each other
        
        Args:
            prompt: Initial question
            rounds: Number of debate rounds
        
        Returns:
            List of response dictionaries, one per round
        """
        print(f"\n🏛️  OKArchitect Debate Mode: {rounds} rounds\n")
        print(f"Topic: {prompt}\n")
        print("=" * 60)
        
        all_rounds = []
        context = f"Initial topic: {prompt}\n\n"
        
        for round_num in range(1, rounds + 1):
            print(f"\n🔄 Round {round_num}/{rounds}")
            print("=" * 60)
            
            round_responses = {}
            
            for member in self.council:
                debate_prompt = f"Respond to the ongoing discussion:\n{context}"
                response = self.consult_member(member, debate_prompt, timeout=120)
                round_responses[member.name] = response
                
                print(f"\n🗣️  **{member.name}**:")
                print(f"{response}")
                print("-" * 60)
                
                # Add to debate context
                context += f"\n{member.name}: {response}\n"
            
            all_rounds.append(round_responses)
            
            # Ask if user wants to continue
            if round_num < rounds:
                continue_debate = input(f"\n🔄 Continue to round {round_num + 1}? (y/n/auto): ").strip().lower()
                if continue_debate == 'n':
                    break
                elif continue_debate != 'auto' and continue_debate != 'y':
                    break
        
        return all_rounds
    
    def synthesize_decision(self, responses: Dict[str, str]) -> str:
        """
        Have the Reasoner synthesize all perspectives into a final decision
        """
        print("\n🎯 Synthesizing final decision...")
        
        context = "Council perspectives:\n\n"
        for member_name, response in responses.items():
            context += f"{member_name}: {response}\n\n"
        
        synthesis_prompt = f"{context}\nBased on all these perspectives, provide a synthesized final recommendation or decision:"
        
        reasoner = self.council[0]  # Reasoner is first in list
        final_decision = self.consult_member(reasoner, synthesis_prompt, timeout=120)
        
        print(f"\n✅ **Final Decision** (by {reasoner.name}):")
        print(final_decision)
        print("=" * 60)
        
        return final_decision
    
    def interactive_mode(self):
        """Interactive CLI for the OKArchitect council"""
        print("\n" + "=" * 60)
        print("🏗️  OKArchitect - Specialized AI Council")
        print("    For EngAIn, ZW, AP Rules, and Game Architecture")
        print("=" * 60)
        print("\nCouncil Members:")
        for member in self.council:
            print(f"  • {member.name}: {member.specialty}")
        print("\nCommands:")
        print("  consult [question]  - Ask the full council")
        print("  debate [question]   - Multi-round debate mode")
        print("  ask [name] [q]      - Ask specific member")
        print("  synthesize          - Get final decision from last consult")
        print("  history             - Show conversation history")
        print("  help                - Show this help")
        print("  exit                - Quit OKArchitect")
        print("=" * 60)
        
        last_responses = None
        
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
                    print("  consult [question]  - Ask the full council")
                    print("  debate [question]   - Multi-round debate mode")
                    print("  ask [name] [q]      - Ask specific member")
                    print("  synthesize          - Get final decision")
                    print("  history             - Show conversation history")
                    
                elif user_input.lower().startswith('consult '):
                    question = user_input[8:].strip()
                    last_responses = self.consult_council(question)
                    
                elif user_input.lower().startswith('debate '):
                    question = user_input[7:].strip()
                    self.debate_mode(question)
                    
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
                
                elif user_input.lower() == 'synthesize':
                    if last_responses:
                        self.synthesize_decision(last_responses)
                    else:
                        print("No recent consultation to synthesize. Use 'consult' first.")
                
                elif user_input.lower() == 'history':
                    if not self.conversation_history:
                        print("No conversation history yet.")
                    else:
                        print(f"\n📜 Conversation History ({len(self.conversation_history)} consultations):")
                        for i, entry in enumerate(self.conversation_history, 1):
                            print(f"\n{i}. {entry['prompt']}")
                            print(f"   Members responded: {', '.join(entry['responses'].keys())}")
                
                else:
                    # Treat as implicit consult
                    last_responses = self.consult_council(user_input)
                    
            except KeyboardInterrupt:
                print("\n\n👋 OKArchitect session interrupted.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


def main():
    """Main entry point for OKArchitect"""
    import argparse
    
    parser = argparse.ArgumentParser(description="OKArchitect - Specialized AI Council for EngAIn Development")
    parser.add_argument('--url', default='http://localhost:11434/api/generate',
                       help='Ollama API URL')
    parser.add_argument('--quick', '-q', metavar='QUESTION',
                       help='Quick consultation (non-interactive)')
    parser.add_argument('--debate', '-d', metavar='TOPIC',
                       help='Start debate mode on a topic')
    parser.add_argument('--rounds', type=int, default=2,
                       help='Number of debate rounds (default: 2)')
    
    args = parser.parse_args()
    
    architect = OKArchitect(base_url=args.url)
    
    if args.quick:
        # Quick consultation mode
        architect.consult_council(args.quick)
    elif args.debate:
        # Debate mode
        architect.debate_mode(args.debate, rounds=args.rounds)
    else:
        # Interactive mode
        architect.interactive_mode()


if __name__ == "__main__":
    main()
