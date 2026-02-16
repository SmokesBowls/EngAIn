#!/usr/bin/env python3
"""
master_pipeline.py - Unified controller for ZW narrative pipeline
Runs all passes from raw text to game scenes with one command.
"""

import argparse
import subprocess
import sys
import os
from pathlib import Path
from typing import List, Optional


class PipelineController:
    """Master controller for ZW narrative processing pipeline"""
    
    def __init__(self, base_dir: Path = Path(".")):
        self.base_dir = base_dir
        self.pass_scripts = {
            "pass1": self.base_dir / "pass1_explicit.py",
            "pass2": self.base_dir / "pass2_enhanced.py",
            "pass3": self.base_dir / "pass3_merge.py",
            "pass4": self.base_dir / "pass4_zon_bridge.py",
            "pass5": self.base_dir / "pass5_game_bridge.py",
        }
        
    def run_pass(self, script_path: Path, args: List[str]) -> bool:
        """Execute a single pass script"""
        try:
            cmd = [sys.executable, str(script_path)] + args
            print(f"▶ Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Error in {script_path.name}:")
                print(result.stderr)
                return False
            
            print(result.stdout.strip())
            return True
            
        except FileNotFoundError:
            print(f"❌ Script not found: {script_path}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def run_full_pipeline(self, input_file: Path, output_dir: Path = None, 
                          era: str = "Unknown", location: str = "Unknown") -> bool:
        """Run complete pipeline from raw text to game scenes"""
        
        if output_dir is None:
            output_dir = self.base_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Stage 1: Text structuring
        print("\n" + "="*60)
        print("STAGE 1: Text Structure Extraction")
        print("="*60)
        
        pass1_output = output_dir / f"out_pass1_{input_file.stem}.txt"
        if not self.run_pass(self.pass_scripts["pass1"], [str(input_file), str(pass1_output)]):
            return False
        
        # Stage 2: Semantic inference
        print("\n" + "="*60)
        print("STAGE 2: Semantic Inference")
        print("="*60)
        
        if not self.run_pass(self.pass_scripts["pass2"], [str(pass1_output)]):
            return False
        
        pass2_output = output_dir / f"out_pass2_{input_file.stem}.metta"
        
        # Stage 3: Merge structure and inference
        print("\n" + "="*60)
        print("STAGE 3: Data Merging")
        print("="*60)
        
        if not self.run_pass(self.pass_scripts["pass3"], [str(pass1_output), str(pass2_output)]):
            return False
        
        pass3_output = output_dir / f"zonj_{input_file.stem}.txt"
        
        # Stage 4: ZON conversion
        print("\n" + "="*60)
        print("STAGE 4: ZON Memory Fabric Conversion")
        print("="*60)
        
        pass4_args = [
            str(pass3_output),
            "--era", era,
            "--location", location,
            "--output-dir", str(output_dir)
        ]
        if not self.run_pass(self.pass_scripts["pass4"], pass4_args):
            return False
        
        zon_output = output_dir / f"{input_file.stem}.zonj.json"
        
        # Stage 5: Game bridge
        print("\n" + "="*60)
        print("STAGE 5: Game Scene Generation")
        print("="*60)
        
        if not self.run_pass(self.pass_scripts["pass5"], [str(zon_output), "--output", str(output_dir / "game_scenes")]):
            return False
        
        return True
    
    def run_custom_pipeline(self, passes: List[str], **kwargs) -> bool:
        """Run only specified passes"""
        pass_sequence = {
            "pass1": ("pass1_explicit.py", ["input.txt"]),
            "pass2": ("pass2_enhanced.py", ["out_pass1_*.txt"]),
            "pass3": ("pass3_merge.py", ["pass1_output.txt", "pass2_output.metta"]),
            "pass4": ("pass4_zon_bridge.py", ["zonj_scene.json"]),
            "pass5": ("pass5_game_bridge.py", ["zonj_scene.zonj.json"]),
        }
        
        for pass_name in passes:
            if pass_name not in pass_sequence:
                print(f"❌ Unknown pass: {pass_name}")
                return False
            
            script_name, default_args = pass_sequence[pass_name]
            script_path = self.base_dir / script_name
            
            # In real implementation, you'd parse kwargs for specific arguments
            print(f"\n▶ Running {pass_name}: {script_name}")
            if not self.run_pass(script_path, default_args):  # Simplified
                return False
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description="ZW Narrative Processing Pipeline - Master Controller"
    )
    parser.add_argument(
        "input_file", 
        help="Input raw text file"
    )
    parser.add_argument(
        "--output-dir", 
        default="./output",
        help="Output directory (default: ./output)"
    )
    parser.add_argument(
        "--era",
        default="Unknown",
        help="Temporal era for ZON anchoring (e.g., FirstAge, ModernEra)"
    )
    parser.add_argument(
        "--location",
        default="Unknown",
        help="Location for ZON anchoring (e.g., Beach, Citadel, Forest)"
    )
    parser.add_argument(
        "--passes",
        nargs="+",
        choices=["pass1", "pass2", "pass3", "pass4", "pass5"],
        help="Run only specific passes"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip intermediate validation steps"
    )
    
    args = parser.parse_args()
    
    controller = PipelineController(Path("."))
    input_path = Path(args.input_file)
    
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)
    
    if args.passes:
        # Run custom pass sequence
        success = controller.run_custom_pipeline(args.passes, **vars(args))
    else:
        # Run full pipeline
        success = controller.run_full_pipeline(
            input_path,
            Path(args.output_dir),
            args.era,
            args.location
        )
    
    if success:
        print("\n" + "="*60)
        print("✅ PIPELINE COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Output directory: {Path(args.output_dir).absolute()}")
    else:
        print("\n❌ PIPELINE FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
