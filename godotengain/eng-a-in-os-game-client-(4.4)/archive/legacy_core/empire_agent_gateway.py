"""
empire_agent_gateway.py - The Contract Between Agents and Empire

This is THE interface between meta-agents (Trae) and world governance (Empire).

Flow:
Meta-Agent (Trae) → Gateway → Validation → Empire → World

Prevents:
- Direct world mutation by agents
- Authority bypass
- Canon corruption
- Replay breakage
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from empire_mr import Empire, Command
from ap_core import check_ap
from canon import can_edit, is_canonical
from reality_mode import get_context
from intent_shadow import record_intent
from history_xeon import commit_event

@dataclass
class Decision:
    """
    Gateway decision on an agent command.
    
    Records: accepted/rejected + reason + metadata
    """
    accepted: bool
    reason: str
    command_id: str
    issuer: str
    authority_level: int
    timestamp: datetime
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class AgentGateway:
    """
    The gateway between meta-agents and Empire.
    
    Responsibilities:
    1. Validate authority (can issuer do this?)
    2. Check reality mode (mutations allowed?)
    3. Validate against AP rules (legal?)
    4. Record in shadow (if rejected)
    5. Route to Empire (if accepted)
    6. Record in history (if executed)
    """
    
    def __init__(self, empire: Empire):
        self.empire = empire
        self._command_counter = 0
    
    def submit_command(self,
                      issuer_id: str,
                      authority_level: int,
                      command: Command,
                      source: str = "agent") -> Decision:
        """
        Submit a command from a meta-agent.
        
        Args:
            issuer_id: Who is issuing ("trae", "human", "council")
            authority_level: Tier (1=AI, 2=soft, 3=hard)
            command: The command to execute
            source: Source system ("trae", "human_cli", etc.)
        
        Returns: Decision (accepted/rejected with reason)
        """
        
        command_id = f"cmd_{self._command_counter}"
        self._command_counter += 1
        
        # ===============================================================
        # STEP 1: Reality Mode Check
        # ===============================================================
        reality = get_context()
        
        # FINALIZED scenes can't be edited (unless Tier 3+ override)
        if reality.is_canonical() and authority_level < 3:
            reason = f"Scene is FINALIZED - requires Tier 3+ authority (have Tier {authority_level})"
            
            # Record rejection in shadow
            record_intent(
                issuer=issuer_id,
                command=command.__dict__,
                reason_rejected=reason,
                scene_id=reality.scene_id,
                source=source
            )
            
            return Decision(
                accepted=False,
                reason=reason,
                command_id=command_id,
                issuer=issuer_id,
                authority_level=authority_level,
                timestamp=datetime.now(),
                metadata={"reality_mode": reality.mode.value}
            )
        
        # REPLAY mode - no mutations allowed
        if not reality.allows_mutation():
            reason = "REPLAY mode - mutations not allowed"
            
            record_intent(
                issuer=issuer_id,
                command=command.__dict__,
                reason_rejected=reason,
                scene_id=reality.scene_id,
                source=source
            )
            
            return Decision(
                accepted=False,
                reason=reason,
                command_id=command_id,
                issuer=issuer_id,
                authority_level=authority_level,
                timestamp=datetime.now()
            )

        # ===============================================================
        # STEP 1.5: Complex AP Rules (Pre-execution Vetting)
        # ===============================================================
        from ap_complex_rules import check_complex_rules
        
        # Convert Command and Empire objects to format expected by complex rules
        # (Kernel state is needed for vetting)
        command_data = vars(command)
        if command.system == "combat" and command.events:
            # Inject primary combat event fields for simplified rule checking
            evt = command.events[0]
            if hasattr(evt, 'source_id'):
                command_data["attacker"] = evt.source_id
                command_data["target"] = evt.target_id
                command_data["amount"] = evt.amount
                command_data["action"] = "attack"

        violations = check_complex_rules(command_data, self.empire.world_state)
        
        if violations:
            reason = f"Complex Rule Violation: {violations[0].message}"
            
            record_intent(
                issuer=issuer_id,
                command=command.__dict__,
                reason_rejected=reason,
                scene_id=reality.scene_id,
                source=source
            )
            
            return Decision(
                accepted=False,
                reason=reason,
                command_id=command_id,
                issuer=issuer_id,
                authority_level=authority_level,
                timestamp=datetime.now(),
                metadata={"violation_id": violations[0].rule_id}
            )
        
        # ===============================================================
        # STEP 2: Empire Execution
        # ===============================================================
        result = self.empire.execute(command)
        
        # ===============================================================
        # STEP 3: Record Result
        # ===============================================================
        if result['accepted']:
            # Success - record in history (if canonical mode)
            if reality.is_canonical():
                commit_event(
                    scene_id=reality.scene_id or "default",
                    event_data=command.__dict__,
                    snapshot_before=result.get('previous_state', {}),
                    snapshot_after=result.get('state', {}),
                    cause=f"{issuer_id} via {source}: {command.system} command",
                    mode=reality.get_history_mode()
                )
            
            return Decision(
                accepted=True,
                reason=result['authority_reason'],
                command_id=command_id,
                issuer=issuer_id,
                authority_level=authority_level,
                timestamp=datetime.now(),
                metadata={
                    "tick": result.get('tick'),
                    "reality_mode": reality.mode.value
                }
            )
        else:
            # Rejected by Empire - record in shadow
            record_intent(
                issuer=issuer_id,
                command=command.__dict__,
                reason_rejected=result['reason'],
                scene_id=reality.scene_id,
                source=source
            )
            
            return Decision(
                accepted=False,
                reason=result['reason'],
                command_id=command_id,
                issuer=issuer_id,
                authority_level=authority_level,
                timestamp=datetime.now()
            )
    
    def submit_trae_command(self, command: Command) -> Decision:
        """
        Convenience method for Trae Agent commands.
        
        Trae is always Tier 1 (AI actor).
        """
        return self.submit_command(
            issuer_id="trae",
            authority_level=1,  # Tier 1 - AI actor
            command=command,
            source="trae_agent"
        )
    
    def submit_human_command(self, command: Command, 
                           override_level: int = 2) -> Decision:
        """
        Convenience method for human commands.
        
        Default: Tier 2 (soft override)
        Can be Tier 3 (hard override) for emergency
        """
        return self.submit_command(
            issuer_id="human",
            authority_level=override_level,
            command=command,
            source="human_cli"
        )

# Global gateway (initialized with empire)
_global_gateway = None

def initialize_gateway(empire: Empire):
    """Initialize the global agent gateway"""
    global _global_gateway
    _global_gateway = AgentGateway(empire)
    return _global_gateway

def submit_command(issuer_id: str, authority_level: int, 
                  command: Command, source: str = "agent") -> Decision:
    """Submit command through global gateway"""
    if _global_gateway is None:
        raise RuntimeError("Gateway not initialized - call initialize_gateway() first")
    return _global_gateway.submit_command(issuer_id, authority_level, command, source)

def submit_trae_command(command: Command) -> Decision:
    """Submit Trae command through global gateway"""
    if _global_gateway is None:
        raise RuntimeError("Gateway not initialized - call initialize_gateway() first")
    return _global_gateway.submit_trae_command(command)

def submit_human_command(command: Command, override_level: int = 2) -> Decision:
    """Submit human command through global gateway"""
    if _global_gateway is None:
        raise RuntimeError("Gateway not initialized - call initialize_gateway() first")
    return _global_gateway.submit_human_command(command, override_level)
