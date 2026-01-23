#!/usr/bin/env python3
"""
narrative_to_game.py - Unified Pass 1-5 Pipeline

Single command: Narrative text → Game scene JSON
"""

import sys
import subprocess
from pathlib import Path
import argparse
import json
import os


class UnifiedPipeline:
    """Runs complete narrative → game pipeline"""
    
    def __init__(self, work_dir: Path = None):
        self.work_dir = work_dir or Path('./pipeline_work')
        self.work_dir.mkdir(exist_ok=True)
        self.root_dir = Path.cwd()
    
    def process_chapter(self, input_file: Path, output_dir: Path) -> Path:
        """Run full pipeline on one chapter"""
        
        print(f"\n{'='*60}")
        print(f"Processing: {input_file.name}")
        print(f"{'='*60}\n")
        
        base_name = input_file.stem
        
        # Pass 1: Segmentation → out_pass1_*.txt (respects output path)
        print("Pass 1: Segmentation...")
        pass1_out = self.work_dir / f"out_pass1_{base_name}.txt"
        subprocess.run([
            'python3', str(self.root_dir / 'pass1_explicit.py'),
            str(input_file.absolute()),
            str(pass1_out)
        ], check=True)
        
        # Pass 2: Inference → out_pass2_*.metta (writes to CWD!)
        # Pass 3: Merge → zonj_*.txt (writes to CWD!)
        # Solution: Run both from work_dir
        print("Pass 2: Inference...")
        print("Pass 3: Merge...")
        
        os.chdir(self.work_dir)
        try:
            # Pass 2 (in work_dir, reads pass1 output, writes to CWD)
            subprocess.run([
                'python3', str(self.root_dir / 'pass2_core.py'),
                f"out_pass1_{base_name}.txt"
            ], check=True)
            
            # Pass 3 (in work_dir, reads pass1+pass2, writes to CWD)
            subprocess.run([
                'python3', str(self.root_dir / 'pass3_merge.py'),
                f"out_pass1_{base_name}.txt",
                f"out_pass2_{base_name}.metta"
            ], check=True)
        finally:
            os.chdir(self.root_dir)
        
        pass3_out = self.work_dir / f"zonj_out_pass1_{base_name}.txt"
        
        # Pass 4: ZON Bridge
        print("Pass 4: ZON Bridge...")
        
        zonj_txt = self.work_dir / f"zonj_out_pass1_{base_name}.txt"
        
        subprocess.run([
            'python3',
            str(self.root_dir / 'pass4_zon_bridge.py'),
            str(zonj_txt),
            '--output-dir',
            str(self.work_dir)
        ], check=True)
        
        # Pass 4 writes out_pass1_*.zonj.json
        pass4_out = self.work_dir / f"out_pass1_{base_name}.zonj.json"
        
        # Pass 5: Game Bridge → game scene JSON
        print("Pass 5: Game Bridge...")
        output_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            'python3', str(self.root_dir / 'pass5_game_bridge.py'),
            str(pass4_out),
            '--output', str(output_dir)
        ], check=True)
        
        # Find generated game scene
        with pass4_out.open('r') as f:
            zon_data = json.load(f)
        
        scene_id = zon_data.get('@id', 'unknown')
        if scene_id.startswith('scene.'):
            scene_id = scene_id[6:]
        
        game_scene = output_dir / f"{scene_id}.json"
        
        print(f"\n✓ Complete: {game_scene.name}")
        
        # Show summary
        with game_scene.open('r') as f:
            scene_data = json.load(f)
        
        print(f"  Characters: {len(scene_data.get('entities', []))}")
        print(f"  Events: {len(scene_data.get('events', []))}")
        print(f"  Location: {scene_data.get('metadata', {}).get('where', 'Unknown')}")
        
        return game_scene


def main():
    parser = argparse.ArgumentParser(description='Unified narrative → game pipeline')
    parser.add_argument('inputs', nargs='+', help='Input narrative files')
    parser.add_argument('--output', default='./game_scenes', help='Output directory')
    parser.add_argument('--work-dir', default='./pipeline_work', help='Working directory')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    work_dir = Path(args.work_dir)
    
    pipeline = UnifiedPipeline(work_dir=work_dir)
    
    results = []
    for input_path in args.inputs:
        input_file = Path(input_path)
        
        if not input_file.exists():
            print(f"⚠ File not found: {input_file}")
            continue
        
        try:
            result = pipeline.process_chapter(input_file, output_dir)
            results.append(result)
        except Exception as e:
            print(f"✗ Failed: {input_file.name}")
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"✓ Pipeline complete!")
    print(f"  Processed: {len(results)} chapter(s)")
    print(f"  Output: {output_dir}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
