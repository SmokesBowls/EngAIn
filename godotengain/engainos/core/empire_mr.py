"""
empire_mr.py - Engine-Agnostic Orchestration Layer

Authority Model: "AI First with Human Overreach"

The world runs itself (AI actors).
The human can intervene (overreach).

Authority Tiers:
- Tier 0: Physical Law (kernel execution)
- Tier 1: World Actors (AI factions)
- Tier 2: Human Soft (suggestions, vetos)
- Tier 3: Human Hard (overrides, pause)
- Tier 4: Debug God (rewind, inspect)
"""

from dataclasses import dataclass
from typing import Dict, Callable, Any, List, Tuple
from copy import deepcopy

@dataclass
class Command:
    """
    A command issued by an actor (AI or human).
    
    issuer: Who issued it ("ai:faction_red", "human", etc.)
    authority_level: Tier (1=AI, 2=soft, 3=hard, 4=debug)
    system: Which kernel to route to ("combat", "spatial", etc.)
    events: Domain events to execute
    """
    issuer: str
    authority_level: int
    system: str
    events: List[Any]
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class Empire:
    """
    Constitutional government for game systems.
    
    Enforces authority hierarchy.
    Routes commands to pure kernels.
    Owns world state.
    Enables replay.
    """
    
    def __init__(self, initial_state: Dict, kernels: Dict[str, Callable]):
        self.world_state = initial_state
        self.initial_state = deepcopy(initial_state)
        self.kernels = kernels
        self.tick = 0
        self.command_log = []  # For replay
        
    def can_execute(self, command: Command) -> Tuple[bool, str]:
        """
        Authority check - does this command have permission?
        
        Returns: (allowed: bool, reason: str)
        """
        
        # Tier 4: Debug god mode (always allowed)
        if command.authority_level >= 4:
            return True, "Authority: Debug god mode"
        
        # Tier 3: Human hard override (always allowed)
        if command.authority_level == 3:
            return True, "Authority: Human hard override"
        
        # Tier 2: Human soft (check if reasonable)
        if command.authority_level == 2:
            return self._check_soft_override(command)
        
        # Tier 1: AI actors (check resources, cooldowns, treaties)
        if command.authority_level == 1:
            return self._ai_allowed(command)
        
        # Tier 0: Physical law (kernels always execute if called)
        if command.authority_level == 0:
            return True, "Authority: Physical law"
        
        return False, "Invalid authority level"
    
    def _ai_allowed(self, command: Command) -> Tuple[bool, str]:
        """
        Check if AI command is allowed.
        
        v0: Always true (world runs freely)
        v1: Check cooldowns, resources, turn order
        v2: Check treaties, alliances, constraints
        """
        # For now: AI is always allowed (world runs itself)
        return True, "AI actor authorized"
    
    def _check_soft_override(self, command: Command) -> Tuple[bool, str]:
        """
        Check if human soft override is reasonable.
        
        Soft overrides can be rejected if they violate world logic.
        
        v0: Always accepted
        v1: Check if aligned with faction goals
        v2: Check if consistent with physics/lore
        """
        # For now: Soft overrides accepted (human is supervisor)
        return True, "Soft override accepted"
    
    def execute(self, command: Command) -> Dict:
        """
        Execute command through appropriate kernel.
        
        Flow:
        1. Authority check
        2. Get kernel
        3. Execute kernel (pure function)
        4. Update world state
        5. Log for replay
        """
        
        # 1. Authority check
        allowed, reason = self.can_execute(command)
        if not allowed:
            return {
                "accepted": False,
                "reason": reason,
                "tick": self.tick,
                "command": command
            }
        
        # 2. Get kernel
        if command.system not in self.kernels:
            return {
                "accepted": False,
                "reason": f"Unknown system: {command.system}",
                "tick": self.tick
            }
        
        kernel = self.kernels[command.system]
        
        # 3. Execute kernel (pure function - snapshot in, snapshot out)
        try:
            # Get current state for this specific system
            if isinstance(self.world_state, dict):
                # Multi-system orchestrator mode
                current_state = self.world_state.get(command.system)
                if current_state is None:
                    return {
                        "accepted": False,
                        "reason": f"System '{command.system}' not in world state",
                        "tick": self.tick
                    }
            else:
                # Single-system mode
                current_state = self.world_state
            
            # Execute kernel with system-specific state
            result = kernel(current_state, command.events)
        except Exception as e:
            return {
                "accepted": False,
                "reason": f"Kernel execution failed: {e}",
                "tick": self.tick
            }
        
        # 4. Update state
        # Update world state with new snapshot
        if isinstance(self.world_state, dict):
            # Multi-system mode - update specific system
            if hasattr(result, 'new_snapshot'):
                self.world_state[command.system] = result.new_snapshot
                alerts = getattr(result, 'alerts', [])
            else:
                self.world_state[command.system] = result
                alerts = []
            new_state = self.world_state[command.system]
        else:
            # Single-system mode - replace entire state
            if hasattr(result, 'new_snapshot'):
                self.world_state = result.new_snapshot
                alerts = getattr(result, 'alerts', [])
            else:
                self.world_state = result
                alerts = []
            new_state = self.world_state
        
        self.tick += 1
        
        # 5. Log for replay
        self.command_log.append({
            "tick": self.tick,
            "command": command,
            "authority_reason": reason
        })
        
        return {
            "accepted": True,
            "authority_reason": reason,
            "tick": self.tick,
            "alerts": alerts,
            "state": self.world_state
        }
    
    def tick_world(self, 
                   ai_commands: List[Command] = None, 
                   human_commands: List[Command] = None) -> List[Dict]:
        """
        Process one world tick.
        
        AI commands run unless human overrides.
        Higher authority commands execute first.
        
        This is the main game loop entry point.
        """
        ai_commands = ai_commands or []
        human_commands = human_commands or []
        
        # Combine and sort by authority (higher first)
        all_commands = sorted(
            ai_commands + human_commands,
            key=lambda c: c.authority_level,
            reverse=True
        )
        
        results = []
        for command in all_commands:
            result = self.execute(command)
            results.append(result)
        
        return results
    
    def replay_from_start(self) -> Dict:
        """
        Replay all commands from initial state.
        
        Proves determinism.
        Enables time travel debugging.
        """
        # Reset to initial state
        replay_state = deepcopy(self.initial_state)
        replay_empire = Empire(replay_state, self.kernels)
        
        # Re-execute all commands
        for entry in self.command_log:
            replay_empire.execute(entry["command"])
        
        return replay_empire.world_state
    
    def get_state_snapshot(self) -> Dict:
        """Get current world state (immutable copy)"""
        return deepcopy(self.world_state)
    
    def can_human_override(self, command: Command) -> bool:
        """
        Check if human COULD override an AI command.
        
        For UI: Show if override button should be enabled.
        """
        return command.authority_level < 3  # Can override anything below hard
