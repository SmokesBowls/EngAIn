#!/usr/bin/env python3
"""
test_full_pipeline.py - Test the complete narrative → ZON pipeline

Demonstrates:
1. Raw narrative → Pass1 (semantic structure)
2. Pass1 → Pass2 (inference extraction)
3. Pass2 → Pass3 (ZONJ merging)
4. ZONJ → Pass4 (ZON memory fabric)

Also tests lore file conversion.
"""

import subprocess
import sys
from pathlib import Path
import json


class PipelineTester:
    """Test the complete EngAIn narrative pipeline"""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.test_dir.mkdir(exist_ok=True)
    
    def create_sample_narrative(self) -> Path:
        """Create a sample narrative for testing"""
        narrative = '''# Part 1: The Awakening

Senareth stood at the edge of the crystalline formation. *Why are they afraid of us?* she wondered.

"We should establish shelter," Vairis said, her tone measured.

The proto-Giants had retreated the moment they saw the vrill-energy manifesting. Fear. That was the dominant emotion.

Senareth thought carefully before responding. "Give them time. They've never seen conscious manipulation before."

*Patience,* she reminded herself. *They need to learn we're not a threat.*

The sun had set over the beach. Wonder. Triumph. Relief. Hope.
'''
        
        narrative_path = self.test_dir / "test_narrative.txt"
        with narrative_path.open("w", encoding="utf-8") as f:
            f.write(narrative)
        
        return narrative_path
    
    def run_pass1(self, narrative_path: Path) -> Path:
        """Run Pass 1: Semantic structure extraction"""
        print("\n=== PASS 1: Semantic Structure Extraction ===")
        
        result = subprocess.run(
            [sys.executable, "pass1_explicit.py", str(narrative_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"PASS1 ERROR: {result.stderr}")
            sys.exit(1)
        
        print(result.stdout)
        
        # Find output file
        output_file = self.test_dir.parent / f"out_pass1_{narrative_path.stem}.txt"
        if not output_file.exists():
            print(f"ERROR: Pass1 output not found: {output_file}")
            sys.exit(1)
        
        # Show sample
        print("\nPass1 Output (first 10 lines):")
        with output_file.open("r") as f:
            for i, line in enumerate(f):
                if i >= 10:
                    break
                print(f"  {line.rstrip()}")
        
        return output_file
    
    def run_pass2(self, pass1_output: Path) -> Path:
        """Run Pass 2: Inference extraction"""
        print("\n=== PASS 2: Inference Extraction ===")
        
        result = subprocess.run(
            [sys.executable, "pass2_core.py", str(pass1_output)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"PASS2 ERROR: {result.stderr}")
            sys.exit(1)
        
        print(result.stdout)
        
        # Find output file
        base_name = pass1_output.stem.replace("out_pass1_", "")
        output_file = self.test_dir.parent / f"out_pass2_{base_name}.metta"
        
        if not output_file.exists():
            print(f"ERROR: Pass2 output not found: {output_file}")
            sys.exit(1)
        
        # Show sample
        print("\nPass2 Output (inferences):")
        with output_file.open("r") as f:
            content = f.read()
            print(content[:500] + "..." if len(content) > 500 else content)
        
        return output_file
    
    def run_pass3(self, pass1_output: Path, pass2_output: Path) -> Path:
        """Run Pass 3: ZONJ merging"""
        print("\n=== PASS 3: ZONJ Merging ===")
        
        result = subprocess.run(
            [sys.executable, "pass3_merge.py", str(pass1_output), str(pass2_output)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"PASS3 ERROR: {result.stderr}")
            sys.exit(1)
        
        print(result.stdout)
        
        # Find output file
        output_file = self.test_dir.parent / f"zonj_{pass1_output.stem}.json"
        
        if not output_file.exists():
            print(f"ERROR: Pass3 output not found: {output_file}")
            sys.exit(1)
        
        # Show sample
        print("\nPass3 Output (ZONJ structure):")
        with output_file.open("r") as f:
            zonj = json.load(f)
            print(f"  Scene ID: {zonj.get('id')}")
            print(f"  Segments: {len(zonj.get('segments', []))}")
            print(f"  First segment: {zonj['segments'][0] if zonj.get('segments') else 'none'}")
        
        return output_file
    
    def run_pass4(self, zonj_path: Path) -> tuple[Path, Path]:
        """Run Pass 4: ZON bridge"""
        print("\n=== PASS 4: ZON Memory Fabric Conversion ===")
        
        result = subprocess.run(
            [sys.executable, "pass4_zon_bridge.py", str(zonj_path),
             "--era", "FirstAge", "--location", "Beach",
             "--output-dir", str(self.test_dir)],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"PASS4 ERROR: {result.stderr}")
            sys.exit(1)
        
        print(result.stdout)
        
        # Find output files
        base_name = zonj_path.stem.replace("zonj_", "")
        zon_path = self.test_dir / f"{base_name}.zon"
        zonj_canon_path = self.test_dir / f"{base_name}.zonj.json"
        
        # Show ZON output
        print("\nZON Output (human-readable):")
        with zon_path.open("r") as f:
            lines = f.readlines()
            for line in lines[:20]:
                print(f"  {line.rstrip()}")
        
        return zon_path, zonj_canon_path
    
    def test_lore_conversion(self, lore_files: list[Path]):
        """Test lore file conversion"""
        print("\n=== LORE FILE CONVERSION ===")
        
        if not lore_files:
            print("No lore files to test")
            return
        
        lore_output_dir = self.test_dir / "lore_zon"
        lore_output_dir.mkdir(exist_ok=True)
        
        for lore_file in lore_files:
            if not lore_file.exists():
                print(f"Skipping missing file: {lore_file}")
                continue
            
            print(f"\nConverting: {lore_file.name}")
            
            result = subprocess.run(
                [sys.executable, "lore_to_zon.py", str(lore_file),
                 "--output-dir", str(lore_output_dir)],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                print(f"  ERROR: {result.stderr}")
                continue
            
            print(result.stdout)


def main():
    print("=" * 70)
    print("ENGAIN NARRATIVE PIPELINE TEST")
    print("=" * 70)
    
    # Setup test directory
    test_dir = Path("./pipeline_test_output")
    tester = PipelineTester(test_dir)
    
    # Create sample narrative
    narrative_path = tester.create_sample_narrative()
    print(f"\nCreated test narrative: {narrative_path}")
    
    try:
        # Run the pipeline
        pass1_output = tester.run_pass1(narrative_path)
        pass2_output = tester.run_pass2(pass1_output)
        pass3_output = tester.run_pass3(pass1_output, pass2_output)
        zon_path, zonj_path = tester.run_pass4(pass3_output)
        
        print("\n" + "=" * 70)
        print("PIPELINE SUCCESS!")
        print("=" * 70)
        print(f"\nFinal outputs:")
        print(f"  ZON (human): {zon_path}")
        print(f"  ZONJ (canon): {zonj_path}")
        
        # Test lore conversion if files exist
        lore_files = [
            Path("/mnt/user-data/uploads/zw_event_seeds_first_age.zw"),
            Path("/mnt/user-data/uploads/zw_character_laws_aeon.zw"),
            Path("/mnt/user-data/uploads/zw_species_origins.zw"),
        ]
        
        tester.test_lore_conversion(lore_files)
        
    except Exception as e:
        print(f"\nPIPELINE FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
