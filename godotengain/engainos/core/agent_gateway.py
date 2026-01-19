cd ~/Downloads/EngAIn/godotengain/engainos/core
cp agent_gateway.py agent_gateway.py.old
cat > agent_gateway.py << 'EOF'
"""
Agent Gateway - Tier validation for AI actors
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from enum import Enum


class AgentTier(Enum):
    """Agent tier levels"""
    TIER_1 = 1
    TIER_2 = 2
    TIER_3 = 3


@dataclass
class TierDecision:
    """Result of tier validation"""
    accepted: bool
    reason: str
    tier: Optional[AgentTier] = None


class AgentGateway:
    """Gateway for AI agent command validation"""
    
    def __init__(self):
        self.agents = {
            "trae": AgentTier.TIER_1,
            "mrlore": AgentTier.TIER_2,
            "clutterbot": AgentTier.TIER_3,
        }
        
        self.mode_requirements = {
            "DRAFT": AgentTier.TIER_1,
            "IMBUED": AgentTier.TIER_1,
            "DREAM": AgentTier.TIER_1,
            "FINALIZED": AgentTier.TIER_3,
            "REPLAY": None,
        }
    
    def validate_command(
        self,
        issuer: str,
        kernel: str,
        method: str,
        args: Dict[str, Any],
        reality_mode: str = "IMBUED"
    ) -> TierDecision:
        """Validate if agent has permission to execute command"""
        issuer_lower = issuer.lower()
        
        if issuer_lower not in self.agents:
            return TierDecision(
                accepted=False,
                reason=f"Unknown agent: {issuer}",
                tier=None
            )
        
        agent_tier = self.agents[issuer_lower]
        required_tier = self.mode_requirements.get(reality_mode)
        
        if required_tier is None:
            return TierDecision(
                accepted=False,
                reason=f"{reality_mode} - read-only mode",
                tier=agent_tier
            )
        
        if agent_tier.value < required_tier.value:
            return TierDecision(
                accepted=False,
                reason=f"{reality_mode} - requires {required_tier.name}",
                tier=agent_tier
            )
        
        return TierDecision(
            accepted=True,
            reason=f"{issuer} (Tier {agent_tier.value}) authorized",
            tier=agent_tier
        )
    
    def route_command(
        self,
        empire,
        issuer: str,
        kernel: str,
        method: str,
        args: Dict[str, Any],
        reality_mode: str = "IMBUED"
    ) -> Dict[str, Any]:
        """Validate and route command through Empire"""
        decision = self.validate_command(
            issuer=issuer,
            kernel=kernel,
            method=method,
            args=args,
            reality_mode=reality_mode
        )
        
        if not decision.accepted:
            return {
                "accepted": False,
                "error": decision.reason
            }
        
        result = empire.execute(
            kernel=kernel,
            method=method,
            args=args,
            issuer=issuer
        )
        
        return {
            "accepted": result.get("accepted", True),
            "result": result
        }
EOF

echo "✓ Fixed agent_gateway.py created"
cd ../tests
PYTHONPATH=../core python3 test_agent_gateway.py
