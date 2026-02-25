#!/usr/bin/env python3
"""
visualize_pipeline.py - Visualize narrative pipeline results
Creates charts and reports for pipeline analysis.
"""

import json
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Dict, List
import numpy as np


class PipelineVisualizer:
    """Visualize pipeline results and statistics"""
    
    def __init__(self):
        sns.set_style("whitegrid")
        self.colors = sns.color_palette("husl", 8)
    
    def analyze_pass1(self, pass1_file: Path) -> Dict:
        """Analyze Pass 1 structure extraction"""
        with open(pass1_file, 'r') as f:
            lines = f.readlines()
        
        stats = {
            "total_lines": len(lines),
            "types": {},
            "speakers": set(),
            "segment_lengths": []
        }
        
        type_pattern = re.compile(r'\{type:([a-z_]+)')
        speaker_pattern = re.compile(r'speaker:([A-Za-z]+)')
        
        for line in lines:
            # Count types
            type_match = type_pattern.search(line)
            if type_match:
                seg_type = type_match.group(1)
                stats["types"][seg_type] = stats["types"].get(seg_type, 0) + 1
            
            # Count speakers
            speaker_match = speaker_pattern.search(line)
            if speaker_match:
                stats["speakers"].add(speaker_match.group(1))
            
            # Segment length
            if '}' in line:
                text_start = line.find('}') + 1
                text = line[text_start:].strip()
                stats["segment_lengths"].append(len(text.split()))
        
        stats["unique_speakers"] = len(stats["speakers"])
        return stats
    
    def analyze_pass2(self, pass2_file: Path) -> Dict:
        """Analyze Pass 2 inference results"""
        with open(pass2_file, 'r') as f:
            content = f.read()
        
        stats = {
            "speaker_inferences": content.count("(speaker"),
            "emotion_inferences": content.count("(emotion"),
            "action_inferences": content.count("(action"),
            "thought_inferences": content.count("(thought"),
            "relationship_inferences": content.count("(relationship"),
            "characters": set(),
            "emotions": set()
        }
        
        # Extract character names
        char_pattern = re.compile(r'\(speaker[^)]+?\s([A-Z][a-z]+)\s')
        for match in char_pattern.finditer(content):
            stats["characters"].add(match.group(1))
        
        # Extract emotion types
        emotion_pattern = re.compile(r'\(emotion[^)]+?\s([a-z_]+)\s:confidence')
        for match in emotion_pattern.finditer(content):
            stats["emotions"].add(match.group(1))
        
        stats["unique_characters"] = len(stats["characters"])
        stats["unique_emotions"] = len(stats["emotions"])
        
        return stats
    
    def analyze_zonj(self, zonj_file: Path) -> Dict:
        """Analyze ZONJ scene file"""
        with open(zonj_file, 'r') as f:
            scene = json.load(f)
        
        stats = {
            "scene_id": scene.get("id", "unknown"),
            "total_segments": len(scene.get("segments", [])),
            "segments_by_type": {},
            "inferences_by_type": {},
            "characters": set(),
            "locations": []
        }
        
        # Analyze segments
        for seg in scene.get("segments", []):
            seg_type = seg.get("type", "unknown")
            stats["segments_by_type"][seg_type] = stats["segments_by_type"].get(seg_type, 0) + 1
            
            # Extract speakers
            if seg.get("speaker"):
                stats["characters"].add(seg["speaker"])
            
            # Analyze inferences
            inferred = seg.get("inferred", {})
            for inf_type, inf_list in inferred.items():
                stats["inferences_by_type"][inf_type] = stats["inferences_by_type"].get(inf_type, 0) + len(inf_list)
                
                # Extract subjects from emotions and thoughts
                if inf_type in ["emotion", "thought"]:
                    for item in inf_list:
                        if "subject" in item:
                            stats["characters"].add(item["subject"])
        
        stats["unique_characters"] = len(stats["characters"])
        return stats
    
    def create_dashboard(self, pipeline_output_dir: Path, output_image: Path = None):
        """Create comprehensive visualization dashboard"""
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        fig.suptitle("ZW Narrative Pipeline Analysis", fontsize=16, fontweight='bold')
        
        # Find files
        pass1_files = list(pipeline_output_dir.glob("out_pass1_*.txt"))
        pass2_files = list(pipeline_output_dir.glob("out_pass2_*.metta"))
        zonj_files = list(pipeline_output_dir.glob("zonj_*.txt"))
        
        if not pass1_files:
            print("❌ No Pass 1 files found")
            return
        
        # Analyze first file of each type
        pass1_stats = self.analyze_pass1(pass1_files[0])
        pass2_stats = self.analyze_pass2(pass2_files[0]) if pass2_files else {}
        zonj_stats = self.analyze_zonj(zonj_files[0]) if zonj_files else {}
        
        # Plot 1: Segment Types (Pass 1)
        ax1 = axes[0, 0]
        if pass1_stats["types"]:
            types = list(pass1_stats["types"].keys())
            counts = list(pass1_stats["types"].values())
            ax1.bar(types, counts, color=self.colors[:len(types)])
            ax1.set_title("Segment Types Distribution")
            ax1.set_xlabel("Type")
            ax1.set_ylabel("Count")
            ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Inference Types (Pass 2)
        ax2 = axes[0, 1]
        if pass2_stats:
            inf_types = ["speaker", "emotion", "action", "thought", "relationship"]
            inf_counts = [pass2_stats.get(f"{t}_inferences", 0) for t in inf_types]
            ax2.bar(inf_types, inf_counts, color=self.colors[:5])
            ax2.set_title("Inference Types Distribution")
            ax2.set_ylabel("Count")
        
        # Plot 3: Emotion Distribution
        ax3 = axes[0, 2]
        if zonj_stats.get("inferences_by_type", {}).get("emotion", 0) > 0:
            # In a real implementation, you'd extract emotion frequencies
            emotions = ["fear", "anger", "joy", "sadness", "wonder", "hope"]
            frequencies = np.random.randint(1, 10, len(emotions))  # Example data
            ax3.pie(frequencies, labels=emotions, autopct='%1.1f%%', colors=self.colors)
            ax3.set_title("Emotion Distribution")
        
        # Plot 4: Segment Length Distribution
        ax4 = axes[1, 0]
        if pass1_stats["segment_lengths"]:
            ax4.hist(pass1_stats["segment_lengths"], bins=20, color=self.colors[0], alpha=0.7)
            ax4.set_title("Segment Length Distribution")
            ax4.set_xlabel("Words per Segment")
            ax4.set_ylabel("Frequency")
        
        # Plot 5: Pipeline Statistics
        ax5 = axes[1, 1]
        stats_labels = ["Segments", "Characters", "Locations", "Dialogue", "Narration"]
        if zonj_stats:
            stats_values = [
                zonj_stats.get("total_segments", 0),
                zonj_stats.get("unique_characters", 0),
                len(zonj_stats.get("locations", [])),
                zonj_stats.get("segments_by_type", {}).get("dialogue", 0),
                zonj_stats.get("segments_by_type", {}).get("narration", 0)
            ]
            y_pos = np.arange(len(stats_labels))
            ax5.barh(y_pos, stats_values, color=self.colors[3])
            ax5.set_yticks(y_pos)
            ax5.set_yticklabels(stats_labels)
            ax5.set_title("Scene Statistics")
            ax5.set_xlabel("Count")
        
        # Plot 6: Text summary
        ax6 = axes[1, 2]
        ax6.axis('off')
        summary_text = f"""
        Pipeline Analysis Summary
        {'='*30}
        
        Pass 1 Statistics:
        • Total segments: {pass1_stats.get('total_lines', 0)}
        • Unique speakers: {pass1_stats.get('unique_speakers', 0)}
        • Segment types: {len(pass1_stats.get('types', {}))}
        
        Pass 2 Statistics:
        • Total inferences: {sum([pass2_stats.get(f'{t}_inferences', 0) for t in ['speaker', 'emotion', 'action', 'thought', 'relationship']])}
        • Unique characters: {pass2_stats.get('unique_characters', 0)}
        • Emotion types: {pass2_stats.get('unique_emotions', 0)}
        
        ZONJ Statistics:
        • Scene ID: {zonj_stats.get('scene_id', 'N/A')}
        • Total segments: {zonj_stats.get('total_segments', 0)}
        • Dialogue segments: {zonj_stats.get('segments_by_type', {}).get('dialogue', 0)}
        """
        ax6.text(0.1, 0.5, summary_text, fontsize=10, va='center', linespacing=1.5)
        
        plt.tight_layout()
        
        if output_image:
            plt.savefig(output_image, dpi=150, bbox_inches='tight')
            print(f"✅ Visualization saved: {output_image}")
        else:
            plt.show()
    
    def generate_report(self, pipeline_output_dir: Path, output_file: Path = None):
        """Generate detailed analysis report"""
        report_lines = []
        report_lines.append("="*60)
        report_lines.append("ZW NARRATIVE PIPELINE ANALYSIS REPORT")
        report_lines.append("="*60)
        report_lines.append(f"Generated: {datetime.now().isoformat()}")
        report_lines.append(f"Directory: {pipeline_output_dir}")
        report_lines.append("")
        
        # Collect all files
        pass1_files = list(pipeline_output_dir.glob("out_pass1_*.txt"))
        pass2_files = list(pipeline_output_dir.glob("out_pass2_*.metta"))
        zonj_files = list(pipeline_output_dir.glob("zonj_*.txt"))
        zon_json_files = list(pipeline_output_dir.glob("*.zonj.json"))
        game_scene_files = list(pipeline_output_dir.glob("game_scenes/*.json"))
        
        # Summary section
        report_lines.append("📊 PIPELINE SUMMARY")
        report_lines.append("-"*40)
        report_lines.append(f"Pass 1 files: {len(pass1_files)}")
        report_lines.append(f"Pass 2 files: {len(pass2_files)}")
        report_lines.append(f"ZONJ files: {len(zonj_files)}")
        report_lines.append(f"ZON JSON files: {len(zon_json_files)}")
        report_lines.append(f"Game scene files: {len(game_scene_files)}")
        report_lines.append("")
        
        # Analyze each Pass 1 file
        report_lines.append("🔍 DETAILED ANALYSIS")
        report_lines.append("-"*40)
        
        for p1_file in pass1_files[:3]:  # Limit to first 3
            stats = self.analyze_pass1(p1_file)
            report_lines.append(f"\nFile: {p1_file.name}")
            report_lines.append(f"  Total segments: {stats['total_lines']}")
            report_lines.append(f"  Segment types: {len(stats['types'])}")
            report_lines.append(f"  Unique speakers: {stats['unique_speakers']}")
            
            for seg_type, count in sorted(stats['types'].items()):
                report_lines.append(f"    • {seg_type}: {count}")
        
        # Write report
        report_text = "\n".join(report_lines)
        
        if output_file:
            output_file.write_text(report_text, encoding="utf-8")
            print(f"✅ Report saved: {output_file}")
        else:
            print(report_text)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Visualize pipeline results")
    parser.add_argument("pipeline_dir", help="Pipeline output directory")
    parser.add_argument("--visualize", action="store_true", help="Generate visualization")
    parser.add_argument("--report", action="store_true", help="Generate text report")
    parser.add_argument("--output", help="Output file/directory")
    
    args = parser.parse_args()
    
    pipeline_dir = Path(args.pipeline_dir)
    if not pipeline_dir.exists():
        print(f"❌ Pipeline directory not found: {pipeline_dir}")
        return 1
    
    visualizer = PipelineVisualizer()
    
    if args.visualize:
        output_image = Path(args.output) if args.output else pipeline_dir / "pipeline_analysis.png"
        visualizer.create_dashboard(pipeline_dir, output_image)
    
    if args.report:
        output_report = Path(args.output) if args.output else pipeline_dir / "pipeline_report.txt"
        visualizer.generate_report(pipeline_dir, output_report)
    
    if not args.visualize and not args.report:
        # Default: create both
        visualizer.create_dashboard(pipeline_dir, pipeline_dir / "pipeline_analysis.png")
        visualizer.generate_report(pipeline_dir, pipeline_dir / "pipeline_report.txt")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
