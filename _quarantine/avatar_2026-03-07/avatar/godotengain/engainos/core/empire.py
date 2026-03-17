"""
Empire - Central orchestration layer for EngAIn

Routes commands to appropriate kernels while enforcing:
1. Reality mode restrictions
2. AI vs Human authority
3. Kernel registration
"""

from typing import Dict, Any, Optional
from enum import Enum


class RealityMode(Enum):
    """Reality mode states"""
    DRAFT = "DRAFT"           # Editable, no enforcement
    IMBUED = "IMBUED"         # ZW/AP bound, soft enforcement
    FINALIZED = "FINALIZED"   # Locked, hard enforcement
    DREAM = "DREAM"           # Sandbox, symbolic
    REPLAY = "REPLAY"         # Read-only, deterministic


class Empire:
    """
    Central command router and reality mode enforcer.
    
    Empire routes commands to registered kernels while enforcing
    reality mode restrictions and authority levels.
    """
    
    def __init__(self):
        self.kernels: Dict[str, Any] = {}
        self.reality_mode = RealityMode.IMBUED
        
        # AI actors (case-insensitive)
        self.ai_actors = {"trae", "mrlore", "clutterbot"}
    
    def register_kernel(self, name: str, kernel: Any):
        """Register a kernel for command routing"""
        self.kernels[name] = kernel
    
    def set_reality_mode(self, mode: str):
        """Set current reality mode"""
        self.reality_mode = RealityMode[mode.upper()]
    
    def get_reality_mode(self) -> str:
        """Get current reality mode"""
        return self.reality_mode.value
    
    def is_ai_actor(self, issuer: str) -> bool:
        """Check if issuer is an AI actor"""
        return issuer.lower() in self.ai_actors
    
    def execute(
        self,
        kernel: str,
        method: str,
        args: Dict[str, Any],
        issuer: str = "human"
    ) -> Dict[str, Any]:
        """
        Execute command on target kernel.
        
        Args:
            kernel: Target kernel name
            method: Method to call
            args: Method arguments
            issuer: Command issuer (AI actor or "human")
            
        Returns:
            Dict with 'accepted' and optional 'error'/'result'
        """
        # Check if kernel exists
        if kernel not in self.kernels:
            return {
                "accepted": False,
                "error": f"Unknown kernel: {kernel}"
            }
        
        # Check reality mode restrictions
        if self.reality_mode == RealityMode.REPLAY:
            return {
                "accepted": False,
                "error": "REPLAY mode - no mutations allowed"
            }
        
        # Check human authority in FINALIZED
        if self.reality_mode == RealityMode.FINALIZED:
            if not self.is_ai_actor(issuer):
                return {
                    "accepted": False,
                    "error": "FINALIZED - humans cannot mutate (Tier 3 required)"
                }
        
        # Route to kernel
        target_kernel = self.kernels[kernel]
        
        # Check if method exists
        if not hasattr(target_kernel, method):
            return {
                "accepted": False,
                "error": f"Kernel {kernel} has no method: {method}"
            }
        
        # Execute method
        try:
            method_func = getattr(target_kernel, method)
            result = method_func(**args)
            
            return {
                "accepted": True,
                "result": result,
                "reason": f"Command executed by {issuer}"
            }
        except Exception as e:
            return {
                "accepted": False,
                "error": f"Execution failed: {str(e)}"
            }
    
    def query_kernel(self, kernel: str, method: str, **kwargs) -> Any:
        """
        Query kernel state (read-only, always allowed).
        
        Args:
            kernel: Target kernel name
            method: Query method
            **kwargs: Method arguments
            
        Returns:
            Query result
        """
        if kernel not in self.kernels:
            raise ValueError(f"Unknown kernel: {kernel}")
        
        target_kernel = self.kernels[kernel]
        
        if not hasattr(target_kernel, method):
            raise ValueError(f"Kernel {kernel} has no method: {method}")
        
        method_func = getattr(target_kernel, method)
        return method_func(**kwargs)
