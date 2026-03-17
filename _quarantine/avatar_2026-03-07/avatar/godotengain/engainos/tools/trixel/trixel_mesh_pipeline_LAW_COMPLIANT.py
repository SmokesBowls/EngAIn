"""
Trixel Mesh Pipeline - Law-Compliant Version
Location: tools/trixel/trixel_mesh_pipeline.py

Integration points:
- Uses mesh_intake.py as HARD GATE
- Generates .trixel manifests (NOT .skin)
- Trixel advises, intake decides, core binds

Philosophy:
- Trixel judges (semantic authority)
- Wings/MeshLab build/clean (geometry)
- mesh_intake enforces (law)
- Core binds (runtime)
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import subprocess
import json

# Import from existing EngAIn law
# These are the authoritative systems
try:
    from mesh_intake import intake_mesh, MeshIntakeResult
    from mesh_manifest import load_trixel_manifest
except ImportError:
    # Fallback for development/testing
    print("Warning: mesh_intake not found. Using stub.")
    def intake_mesh(*args, **kwargs):
        return {"status": "stub"}
    def load_trixel_manifest(*args, **kwargs):
        return {"status": "stub"}


@dataclass
class SemanticIntent:
    """
    Trixel's semantic judgment about what should exist.
    This is advisory input to the law, not the law itself.
    """
    zw_concept: str
    narrative_context: str
    
    # Semantic constraints (Trixel's interpretation)
    constraints: Dict[str, Any]
    region_tags: Dict[str, str]
    
    # Visual validation (Trixel's vision check)
    visual_validation_prompt: str
    required_features: List[str]
    
    # ZW metadata (for AP profile, game logic)
    zw_tags: Dict[str, Any]
    
    # Placeholder determination (for Godot initial spawn)
    placeholder_type: str  # "capsule", "cube", etc.


@dataclass
class TrixelJudgment:
    """
    Trixel's advisory opinion on mesh quality.
    This is NOT authoritative - mesh_intake makes final call.
    """
    visual_match_score: float  # 0.0-1.0
    narrative_alignment: str   # "strong", "acceptable", "weak"
    required_features_present: List[str]
    required_features_missing: List[str]
    advisory_notes: str
    
    @property
    def recommended_accept(self) -> bool:
        """Trixel's recommendation (not binding)"""
        return (
            self.visual_match_score >= 0.7 and
            len(self.required_features_missing) == 0
        )


@dataclass
class MeshArtifact:
    """
    Output from pipeline after mesh_intake validation.
    This represents mesh that PASSED law.
    """
    mesh_path: Path
    trixel_manifest_path: Path
    trixel_judgment: TrixelJudgment
    intake_result: Any  # Result from mesh_intake.py
    law_approved: bool  # Did it pass mesh_intake gate?


class TrixelComposer:
    """
    Trixel's semantic authority role.
    
    Responsibilities:
    1. Extract semantic intent from narrative
    2. Provide visual validation (advisory)
    3. Annotate with semantic metadata
    
    NOT responsible for:
    - Enforcing acceptance (that's mesh_intake)
    - Creating manifests (that's mesh_intake)
    - Binding to entities (that's core)
    """
    
    def extract_intent_from_narrative(
        self,
        narrative: str,
        zw_concept: str
    ) -> SemanticIntent:
        """
        Trixel reads narrative and defines semantic intent.
        This is Trixel's interpretation, subject to law.
        """
        # In production, this uses Trixel's actual vision/language model
        # For now, demonstrate structure
        
        # Determine entity type for AP profile selection
        entity_type = self._classify_entity_type(narrative)
        
        # Determine placeholder for Godot spawning
        placeholder = self._determine_placeholder(entity_type, narrative)
        
        return SemanticIntent(
            zw_concept=zw_concept,
            narrative_context=narrative,
            constraints={
                "height": 2.0,  # Extracted from "towering"
                "armor_type": "heavy",
                "wear_level": "battle_worn"
            },
            region_tags={
                "head": "helmeted_scarred",
                "torso": "heavy_plate",
                "arms": "gauntlets",
                "legs": "greaves"
            },
            visual_validation_prompt=(
                "A tall guard in heavy plate armor. "
                "Battle scars visible. Stern posture. "
                "Well-maintained armor despite wear."
            ),
            required_features=["helmet", "chest_plate", "gauntlets"],
            zw_tags={
                "entity_type": entity_type,
                "ap_profile": "npc_humanoid",  # For mesh_intake
                "role": "guard",
                "interactable": True
            },
            placeholder_type=placeholder
        )
    
    def judge_mesh_quality(
        self,
        mesh_path: Path,
        intent: SemanticIntent
    ) -> TrixelJudgment:
        """
        Trixel's visual judgment - ADVISORY ONLY.
        mesh_intake makes the final call.
        """
        # Render preview for vision model
        preview = self._render_preview(mesh_path)
        
        # Vision model evaluation (stub - real implementation uses Trixel's model)
        visual_score = self._evaluate_visual_match(preview, intent)
        
        # Check required features
        present, missing = self._check_features(preview, intent.required_features)
        
        # Assess narrative alignment
        alignment = self._assess_narrative_alignment(preview, intent)
        
        return TrixelJudgment(
            visual_match_score=visual_score,
            narrative_alignment=alignment,
            required_features_present=present,
            required_features_missing=missing,
            advisory_notes=self._generate_notes(visual_score, alignment, missing)
        )
    
    def _classify_entity_type(self, narrative: str) -> str:
        """Classify entity for AP profile selection"""
        narrative_lower = narrative.lower()
        if "guard" in narrative_lower or "soldier" in narrative_lower:
            return "npc_humanoid"
        elif "door" in narrative_lower or "gate" in narrative_lower:
            return "architecture_door"
        elif "chest" in narrative_lower:
            return "container"
        return "prop_generic"
    
    def _determine_placeholder(self, entity_type: str, narrative: str) -> str:
        """Determine Godot placeholder primitive"""
        if entity_type == "npc_humanoid":
            return "capsule"
        elif entity_type == "architecture_door":
            return "cube"
        elif entity_type == "container":
            return "cube"
        return "cube"
    
    def _render_preview(self, mesh_path: Path) -> Path:
        """Render mesh for vision evaluation"""
        preview_path = mesh_path.with_suffix('.preview.png')
        # Stub - would use Godot headless or simple renderer
        return preview_path
    
    def _evaluate_visual_match(self, preview: Path, intent: SemanticIntent) -> float:
        """Vision model scores match to intent"""
        # Stub - Trixel's actual vision model would run here
        return 0.85
    
    def _check_features(
        self,
        preview: Path,
        required: List[str]
    ) -> Tuple[List[str], List[str]]:
        """Check which required features are present"""
        # Stub - vision model would detect features
        return required, []
    
    def _assess_narrative_alignment(
        self,
        preview: Path,
        intent: SemanticIntent
    ) -> str:
        """Assess how well mesh matches narrative"""
        # Stub - would use vision + language model
        return "strong"
    
    def _generate_notes(
        self,
        score: float,
        alignment: str,
        missing: List[str]
    ) -> str:
        """Generate advisory notes"""
        if score >= 0.85:
            return f"Excellent match. {alignment.capitalize()} narrative alignment."
        elif score >= 0.7:
            return f"Acceptable match. {alignment.capitalize()} alignment."
        else:
            return f"Weak match. Missing features: {', '.join(missing)}"


class WingsMeshBuilder:
    """
    Wings 3D adapter - geometry creation.
    Trixel never touches this.
    """
    
    def build_from_intent(
        self,
        intent: SemanticIntent,
        template_base: Optional[Path] = None
    ) -> Path:
        """
        Build mesh in Wings from semantic intent.
        Returns raw OBJ path.
        """
        output_dir = Path("assets/meshes/raw")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"{intent.zw_concept}.obj"
        
        # Stub - real implementation would:
        # 1. Generate procedural base, or
        # 2. Call Wings 3D scripting, or
        # 3. Prompt human to model in Wings
        
        output_path.write_text("# OBJ placeholder\n")
        return output_path


class MeshLabSanitizer:
    """
    MeshLab adapter - automated cleanup.
    Runs headless, no Trixel involvement.
    """
    
    def sanitize(self, raw_mesh: Path) -> Path:
        """
        Clean mesh through MeshLab pipeline.
        Returns clean OBJ path.
        """
        output_dir = Path("assets/meshes/clean")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / f"{raw_mesh.stem}_clean.obj"
        
        # Generate MeshLab script
        script_path = self._create_cleanup_script()
        
        # Run headless (if MeshLab installed)
        try:
            subprocess.run([
                'meshlabserver',
                '-i', str(raw_mesh),
                '-o', str(output_path),
                '-s', str(script_path)
            ], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            # MeshLab not available - copy as-is
            import shutil
            shutil.copy(raw_mesh, output_path)
        
        return output_path
    
    def _create_cleanup_script(self) -> Path:
        """Generate MeshLab filter script"""
        script_path = Path('/tmp/meshlab_cleanup.mlx')
        script_content = """
<!DOCTYPE FilterScript>
<FilterScript>
    <filter name="Remove Duplicate Vertices"/>
    <filter name="Remove Unreferenced Vertices"/>
    <filter name="Repair non Manifold Edges"/>
    <filter name="Re-Orient all faces coherentely"/>
</FilterScript>
"""
        script_path.write_text(script_content)
        return script_path


class TrixelMeshPipeline:
    """
    Complete authoring pipeline with mesh_intake integration.
    
    Flow:
    1. Trixel extracts intent
    2. Wings builds mesh
    3. MeshLab cleans
    4. Trixel judges (advisory)
    5. mesh_intake enforces (HARD GATE)
    6. Core binds to entities (if approved)
    """
    
    def __init__(self):
        self.trixel = TrixelComposer()
        self.wings = WingsMeshBuilder()
        self.meshlab = MeshLabSanitizer()
    
    def generate_mesh_from_narrative(
        self,
        narrative: str,
        zw_concept: str,
        template_base: Optional[Path] = None
    ) -> MeshArtifact:
        """
        Complete workflow with law enforcement.
        
        Returns MeshArtifact with law_approved flag.
        Only approved meshes are usable in game.
        """
        print(f"\n{'='*70}")
        print(f"TRIXEL MESH PIPELINE: {zw_concept}")
        print(f"{'='*70}")
        
        # Step 1: Trixel extracts semantic intent
        print(f"\n[1/5] Trixel: Extracting semantic intent...")
        intent = self.trixel.extract_intent_from_narrative(narrative, zw_concept)
        print(f"      Entity type: {intent.zw_tags['entity_type']}")
        print(f"      AP profile: {intent.zw_tags['ap_profile']}")
        print(f"      Placeholder: {intent.placeholder_type}")
        
        # Step 2: Wings builds mesh
        print(f"\n[2/5] Wings: Building mesh...")
        raw_mesh = self.wings.build_from_intent(intent, template_base)
        print(f"      Raw: {raw_mesh}")
        
        # Step 3: MeshLab cleans
        print(f"\n[3/5] MeshLab: Sanitizing...")
        clean_mesh = self.meshlab.sanitize(raw_mesh)
        print(f"      Clean: {clean_mesh}")
        
        # Step 4: Trixel judges (advisory)
        print(f"\n[4/5] Trixel: Visual judgment (advisory)...")
        judgment = self.trixel.judge_mesh_quality(clean_mesh, intent)
        print(f"      Visual match: {judgment.visual_match_score:.2f}")
        print(f"      Narrative alignment: {judgment.narrative_alignment}")
        print(f"      Recommendation: {'ACCEPT' if judgment.recommended_accept else 'REJECT'}")
        print(f"      Notes: {judgment.advisory_notes}")
        
        # Step 5: mesh_intake enforces (HARD GATE)
        print(f"\n[5/5] mesh_intake: Law enforcement (HARD GATE)...")
        intake_result = self._submit_to_intake(clean_mesh, intent, judgment)
        
        if intake_result.get("status") == "accepted":
            print(f"      ✓ LAW APPROVED")
            print(f"      Manifest: {intake_result.get('manifest_path')}")
            law_approved = True
        else:
            print(f"      ✗ LAW REJECTED")
            print(f"      Reason: {intake_result.get('reason', 'Unknown')}")
            law_approved = False
        
        print(f"\n{'='*70}")
        
        return MeshArtifact(
            mesh_path=clean_mesh,
            trixel_manifest_path=Path(intake_result.get("manifest_path", "")),
            trixel_judgment=judgment,
            intake_result=intake_result,
            law_approved=law_approved
        )
    
    def _submit_to_intake(
        self,
        mesh_path: Path,
        intent: SemanticIntent,
        judgment: TrixelJudgment
    ) -> Dict[str, Any]:
        """
        Submit mesh to mesh_intake for law enforcement.
        This is the HARD GATE - only mesh_intake decides acceptance.
        """
        try:
            # Call existing mesh_intake system
            result = intake_mesh(
                mesh_path=str(mesh_path),
                zw_concept=intent.zw_concept,
                ap_profile=intent.zw_tags.get("ap_profile", "default"),
                collision_role="solid",
                lod_class="character",
                placeholder_mesh=intent.placeholder_type,
                source_tool="trixel_pipeline",
                
                # Include Trixel's advisory judgment as metadata
                trixel_judgment={
                    "visual_match_score": judgment.visual_match_score,
                    "narrative_alignment": judgment.narrative_alignment,
                    "advisory_notes": judgment.advisory_notes,
                    "recommended_accept": judgment.recommended_accept
                }
            )
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "reason": str(e),
                "manifest_path": None
            }


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """Command-line interface for Trixel pipeline"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python trixel_mesh_pipeline.py <concept> <narrative>")
        print("\nExample:")
        print('  python trixel_mesh_pipeline.py guard_theron "A towering guard"')
        sys.exit(1)
    
    concept = sys.argv[1]
    narrative = " ".join(sys.argv[2:])
    
    pipeline = TrixelMeshPipeline()
    result = pipeline.generate_mesh_from_narrative(narrative, concept)
    
    # Exit code reflects law decision
    sys.exit(0 if result.law_approved else 1)


if __name__ == "__main__":
    main()
