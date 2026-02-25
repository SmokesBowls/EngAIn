"""
trae_observer.py - Automated Failure Analysis Agent

Defense Layer 3: Close the AI learning loop.

Watches shadow memory and generates structured learning signals.
Non-mutating (read-only). Commits analysis to HistoryXeon in DREAM mode.

Flow:
  Shadow Memory (failed intents)
    ↓
  Trae Observer (THIS FILE - pattern detection)
    ↓
  HistoryXeon DREAM mode (structured learning signals)
    ↓
  Trae reads reports (instant actionable feedback)
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from collections import Counter
from datetime import datetime

from intent_shadow import query_intents, get_failure_count, get_recent_intents
from history_xeon import commit_event
from reality_mode import RealityMode


@dataclass
class FailurePattern:
    """Detected pattern in shadow memory"""
    reason: str
    count: int
    percentage: float
    recent_examples: List[Dict]
    recommendation: str


@dataclass
class ShadowReport:
    """
    Structured analysis of shadow memory.
    
    This is what gets committed to HistoryXeon in DREAM mode.
    Trae reads this instead of parsing raw shadow memory.
    """
    timestamp: datetime
    total_failures: int
    unique_reasons: int
    top_patterns: List[FailurePattern]
    affected_issuers: List[str]
    affected_scenes: List[str]
    summary: str
    recommendations: List[str]


class TraeObserver:
    """
    Automated failure analysis agent.
    
    Watches shadow memory (read-only).
    Generates structured learning signals.
    Commits to HistoryXeon in DREAM mode.
    
    NON-MUTATING: Never modifies shadow memory.
    """
    
    def __init__(self, min_pattern_threshold: int = 2):
        self.min_pattern_threshold = min_pattern_threshold
        self.last_analysis_time: Optional[datetime] = None
        self.analysis_count = 0
    
    def analyze_shadow(self, 
                      scene_id: Optional[str] = None,
                      issuer: Optional[str] = None,
                      limit: int = 100) -> ShadowReport:
        """
        Analyze shadow memory and generate structured report.
        
        Args:
            scene_id: Filter to specific scene
            issuer: Filter to specific issuer (e.g. "trae")
            limit: Max intents to analyze
        
        Returns: Structured shadow report
        """
        self.analysis_count += 1
        self.last_analysis_time = datetime.now()
        
        # Query shadow memory (read-only)
        intents = get_recent_intents(n=limit)
        
        # Filter if needed
        if scene_id:
            intents = [i for i in intents if i.scene_id == scene_id]
        if issuer:
            intents = [i for i in intents if i.issuer == issuer]
        
        if not intents:
            return self._empty_report()
        
        # Analyze patterns
        total_failures = len(intents)
        
        # Group by rejection reason
        reason_counter = Counter(i.reason_rejected for i in intents)
        unique_reasons = len(reason_counter)
        
        # Build pattern objects
        patterns = []
        for reason, count in reason_counter.most_common():
            if count < self.min_pattern_threshold:
                continue
            
            percentage = (count / total_failures) * 100
            
            # Get recent examples
            examples = [
                {
                    "issuer": i.issuer,
                    "command": i.command,
                    "scene": i.scene_id,
                    "timestamp": i.timestamp.isoformat()
                }
                for i in intents
                if i.reason_rejected == reason
            ][:3]  # Max 3 examples
            
            # Generate recommendation
            recommendation = self._generate_recommendation(reason, count)
            
            patterns.append(FailurePattern(
                reason=reason,
                count=count,
                percentage=percentage,
                recent_examples=examples,
                recommendation=recommendation
            ))
        
        # Affected entities
        affected_issuers = list(set(i.issuer for i in intents))
        affected_scenes = list(set(i.scene_id for i in intents if i.scene_id))
        
        # Generate summary
        summary = self._generate_summary(total_failures, patterns, affected_issuers)
        
        # Aggregate recommendations
        recommendations = [p.recommendation for p in patterns[:5]]  # Top 5
        
        return ShadowReport(
            timestamp=datetime.now(),
            total_failures=total_failures,
            unique_reasons=unique_reasons,
            top_patterns=patterns,
            affected_issuers=affected_issuers,
            affected_scenes=affected_scenes,
            summary=summary,
            recommendations=recommendations
        )
    
    def _generate_recommendation(self, reason: str, count: int) -> str:
        """Generate actionable recommendation based on failure reason"""
        
        # Pattern matching on common failure types
        reason_lower = reason.lower()
        
        if "stamina" in reason_lower or "insufficient" in reason_lower:
            return f"Check resource availability before issuing commands ({count} failures)"
        
        if "finalized" in reason_lower or "canon" in reason_lower:
            return f"Verify reality mode before mutation attempts ({count} failures)"
        
        if "replay" in reason_lower:
            return f"Avoid mutations during REPLAY mode ({count} failures)"
        
        if "authority" in reason_lower or "tier" in reason_lower:
            return f"Request higher authority tier for protected operations ({count} failures)"
        
        if "treaty" in reason_lower or "alliance" in reason_lower:
            return f"Check faction relationships before hostile actions ({count} failures)"
        
        if "weapon" in reason_lower or "equipment" in reason_lower:
            return f"Verify inventory state before equipment-dependent actions ({count} failures)"
        
        # Generic recommendation
        return f"Pattern detected: '{reason}' ({count} occurrences) - investigate root cause"
    
    def _generate_summary(self, 
                         total: int, 
                         patterns: List[FailurePattern],
                         issuers: List[str]) -> str:
        """Generate human-readable summary"""
        
        if total == 0:
            return "No failures detected in shadow memory."
        
        top_reason = patterns[0].reason if patterns else "Unknown"
        top_count = patterns[0].count if patterns else 0
        
        summary_parts = [
            f"Analyzed {total} failed intent(s)",
            f"Primary failure: '{top_reason}' ({top_count} occurrences)",
            f"Affecting: {', '.join(issuers)}"
        ]
        
        return ". ".join(summary_parts) + "."
    
    def _empty_report(self) -> ShadowReport:
        """Generate empty report when no failures found"""
        return ShadowReport(
            timestamp=datetime.now(),
            total_failures=0,
            unique_reasons=0,
            top_patterns=[],
            affected_issuers=[],
            affected_scenes=[],
            summary="No failures detected in shadow memory.",
            recommendations=[]
        )
    
    def commit_report_to_history(self, 
                                report: ShadowReport,
                                scene_id: str = "shadow_analysis") -> bool:
        """
        Commit shadow report to HistoryXeon in DREAM mode.
        
        This separates learning data from canonical history.
        Trae queries DREAM mode for learning signals.
        
        Args:
            report: Shadow report to commit
            scene_id: Scene identifier (default: shadow_analysis)
        
        Returns: True if committed successfully
        """
        try:
            # Convert report to event data
            event_data = {
                "type": "shadow_analysis",
                "timestamp": report.timestamp.isoformat(),
                "total_failures": report.total_failures,
                "unique_reasons": report.unique_reasons,
                "summary": report.summary,
                "top_patterns": [
                    {
                        "reason": p.reason,
                        "count": p.count,
                        "percentage": p.percentage,
                        "recommendation": p.recommendation
                    }
                    for p in report.top_patterns[:5]  # Top 5 only
                ],
                "recommendations": report.recommendations
            }
            
            # Commit to HistoryXeon in DREAM mode
            commit_event(
                scene_id=scene_id,
                event_data=event_data,
                snapshot_before={},  # Not applicable for meta-analysis
                snapshot_after={},
                cause="Automated shadow memory analysis by TraeObserver",
                mode="DREAM"  # CRITICAL: DREAM mode, not CANON
            )
            
            return True
            
        except Exception as e:
            print(f"Warning: Failed to commit shadow report to history: {e}")
            return False
    
    def get_latest_report_from_history(self, scene_id: str = "shadow_analysis") -> Optional[Dict]:
        """
        Retrieve latest shadow report from HistoryXeon.
        
        Trae uses this to get instant learning signals
        without parsing raw shadow memory.
        """
        from history_xeon import get_history
        
        # Query DREAM mode history
        dream_events = get_history(scene_id, mode="DREAM")
        
        if not dream_events:
            return None
        
        # Get most recent shadow_analysis event
        for event in reversed(dream_events):
            if event.event_data.get("type") == "shadow_analysis":
                return event.event_data
        
        return None


# ================================================================
# GLOBAL OBSERVER INSTANCE
# ================================================================

_global_observer = TraeObserver(min_pattern_threshold=2)


def analyze_and_report(scene_id: Optional[str] = None,
                       issuer: Optional[str] = None,
                       commit_to_history: bool = True) -> ShadowReport:
    """
    Convenience function: Analyze shadow and optionally commit to history.
    
    Args:
        scene_id: Filter to scene
        issuer: Filter to issuer
        commit_to_history: Auto-commit to HistoryXeon DREAM mode
    
    Returns: Shadow report
    """
    report = _global_observer.analyze_shadow(scene_id=scene_id, issuer=issuer)
    
    if commit_to_history and report.total_failures > 0:
        _global_observer.commit_report_to_history(report, scene_id=scene_id or "shadow_analysis")
    
    return report


def get_latest_learning_signal(scene_id: str = "shadow_analysis") -> Optional[Dict]:
    """
    Get latest learning signal from HistoryXeon.
    
    Trae calls this to get instant actionable feedback.
    """
    return _global_observer.get_latest_report_from_history(scene_id)


def print_shadow_report(report: ShadowReport):
    """Print shadow report in human-readable format"""
    print("\n" + "="*60)
    print("SHADOW MEMORY ANALYSIS REPORT")
    print("="*60)
    print(f"Timestamp: {report.timestamp.isoformat()}")
    print(f"Total Failures: {report.total_failures}")
    print(f"Unique Reasons: {report.unique_reasons}")
    print(f"\nSummary: {report.summary}")
    
    if report.top_patterns:
        print(f"\nTop Failure Patterns:")
        for i, pattern in enumerate(report.top_patterns[:5], 1):
            print(f"\n  {i}. {pattern.reason}")
            print(f"     Count: {pattern.count} ({pattern.percentage:.1f}%)")
            print(f"     Recommendation: {pattern.recommendation}")
    
    if report.recommendations:
        print(f"\nActionable Recommendations:")
        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")
    
    print("\n" + "="*60 + "\n")
