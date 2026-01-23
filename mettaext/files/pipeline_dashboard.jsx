import React, { useState } from 'react';
import { FileText, GitBranch, Database, Zap, CheckCircle, AlertCircle } from 'lucide-react';

export default function EngAInPipelineDashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [expandedStage, setExpandedStage] = useState(null);

  const pipelineStages = [
    {
      id: 'pass1',
      name: 'Pass 1: Semantic Structure',
      file: 'pass1_explicit.py',
      input: 'Raw narrative text (.txt)',
      output: 'out_pass1_*.txt',
      description: 'Extracts semantic units: dialogue, narration, internal monologue, scene headers',
      features: [
        'Dialogue speaker detection',
        'Internal monologue extraction (*thoughts*)',
        'Sentence-level narration splitting',
        'Scene header identification'
      ],
      exampleOutput: '{type:dialogue, speaker:Vairis} "We should establish shelter,"'
    },
    {
      id: 'pass2',
      name: 'Pass 2: Inference Extraction',
      file: 'pass2_core.py / pass2_enhanced.py',
      input: 'out_pass1_*.txt',
      output: 'out_pass2_*.metta',
      description: 'Extracts semantic atoms: speakers, emotions, actions, thoughts, relationships',
      features: [
        'Speaker inference (95% confidence)',
        'Pronoun → actor mapping',
        'Emotion detection (wonder, fear, hope, etc.)',
        'Action extraction (retreat, vrill manipulation)',
        'Thought attribution',
        'Character relationship inference (enhanced)'
      ],
      exampleOutput: '(emotion line:39 Senareth fear :confidence 0.9)'
    },
    {
      id: 'pass3',
      name: 'Pass 3: ZONJ Merging',
      file: 'pass3_merge.py',
      input: 'out_pass1_*.txt + out_pass2_*.metta',
      output: 'zonj_*.json',
      description: 'Merges explicit structure with inferred semantics into ZONJ format',
      features: [
        'Future-proof attribute parsing',
        'Tolerant metta parsing',
        'Header attribute preservation',
        'Line-level inference attachment',
        'Scene ID extraction'
      ],
      exampleOutput: '{"type": "scene", "segments": [{"line": 12, "inferred": {...}}]}'
    },
    {
      id: 'pass4',
      name: 'Pass 4: ZON Bridge',
      file: 'pass4_zon_bridge.py',
      input: 'zonj_*.json',
      output: '*.zon + *.zonj.json',
      description: 'Converts ZONJ to ZON4D memory fabric with temporal/spatial anchoring',
      features: [
        'Temporal anchoring (@when)',
        'Spatial anchoring (@where)',
        'Entity extraction and tracking',
        'Scope assignment (narrative/canon/lore)',
        'Dual output: human-readable .zon + canonical .zonj'
      ],
      exampleOutput: '@id: scene.first_contact\n@when: FirstAge.scene_001\n@where: Realm/Physical/Beach'
    },
    {
      id: 'lore',
      name: 'Lore Conversion',
      file: 'lore_to_zon.py',
      input: 'ZW lore files (*.zw)',
      output: '*.zon + *.zonj.json',
      description: 'Converts ZW lore blocks (EVENT_SEED, CHARACTER_LAW, etc.) to ZON format',
      features: [
        'Block type mapping (ZW_EVENT_SEED → event scope)',
        'Era extraction (FirstAge, PreMatter)',
        'Domain/scope inference',
        'Entity relationship extraction',
        'Tag preservation'
      ],
      exampleOutput: '@id: zw_event_seed.genesis\n@scope: event\n@entities: [aeon, vrill]'
    }
  ];

  const architectureNotes = {
    philosophy: [
      'AI Logic Built for AI, Not Humans',
      'World Model as Truth (inspired by Inform 7)',
      'Engine-agnostic content via ZON compilation',
      'Perfect semantic fidelity through roundtrip conversion'
    ],
    core_tech: [
      'ZW (Ziegel Wagga): Semantic data compression (7x reduction)',
      'ZON: 4D declarative memory and temporal state',
      'AP (Anti-Python): Declarative rule systems',
      'ZONJ: Canonical JSON interchange format'
    ],
    workflow: [
      'Raw narrative → Pass1 → Pass2 → Pass3 → Pass4 → ZON memory fabric',
      'Parallel: ZW lore files → lore_to_zon.py → ZON memory fabric',
      'Integration: All ZON blocks merge into unified 4D timeline'
    ]
  };

  const commonIssues = [
    {
      issue: 'Filename mismatch in Pass 3',
      solution: 'Pass3 generates zonj_{pass1_stem}.json - ensure base name matches',
      file: 'pass3_merge.py:543-544'
    },
    {
      issue: 'Speaker inference gaps',
      solution: 'Use pass2_enhanced.py for better character tracking across scenes',
      file: 'pass2_enhanced.py'
    },
    {
      issue: 'Missing temporal metadata',
      solution: 'Pass --era, --location, --start, --end flags to pass4_zon_bridge.py',
      file: 'pass4_zon_bridge.py:361-365'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent mb-2">
            EngAIn Narrative Pipeline
          </h1>
          <p className="text-slate-300 text-lg">
            AI Logic Built for AI, Not Humans • ZW → ZON4D Memory Fabric
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 border-b border-slate-700">
          {['overview', 'pipeline', 'architecture', 'troubleshoot'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-3 font-semibold transition-all ${
                activeTab === tab
                  ? 'text-cyan-400 border-b-2 border-cyan-400'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-cyan-400 mb-4">Quick Start</h2>
              <div className="space-y-4">
                <div className="bg-slate-900/50 p-4 rounded border-l-4 border-green-500">
                  <h3 className="font-bold text-green-400 mb-2">Using the GUI</h3>
                  <code className="text-sm text-slate-300">python3 narrative_pipeline_gui.py</code>
                  <p className="text-sm text-slate-400 mt-2">
                    Complete interface for narrative processing and lore conversion
                  </p>
                </div>
                
                <div className="bg-slate-900/50 p-4 rounded border-l-4 border-blue-500">
                  <h3 className="font-bold text-blue-400 mb-2">Command Line (Full Pipeline)</h3>
                  <pre className="text-xs text-slate-300 bg-slate-950 p-3 rounded mt-2 overflow-x-auto">
{`# Process narrative
python3 pass1_explicit.py narrative.txt
python3 pass2_core.py out_pass1_narrative.txt
python3 pass3_merge.py out_pass1_narrative.txt out_pass2_narrative.metta
python3 pass4_zon_bridge.py zonj_out_pass1_narrative.json --era FirstAge --location Beach

# Convert lore
python3 lore_to_zon.py zw_event_seeds.zw --output-dir ./zon_output`}
                  </pre>
                </div>

                <div className="bg-slate-900/50 p-4 rounded border-l-4 border-purple-500">
                  <h3 className="font-bold text-purple-400 mb-2">Run Tests</h3>
                  <code className="text-sm text-slate-300">python3 test_full_pipeline.py</code>
                  <p className="text-sm text-slate-400 mt-2">
                    Validates complete pipeline with sample data
                  </p>
                </div>
              </div>
            </div>

            {/* File Structure */}
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-cyan-400 mb-4">File Organization</h2>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <h3 className="font-semibold text-purple-400">Pipeline Scripts</h3>
                  <div className="text-sm space-y-1 font-mono">
                    <div className="text-green-400">✓ pass1_explicit.py</div>
                    <div className="text-green-400">✓ pass2_core.py</div>
                    <div className="text-blue-400">✓ pass2_enhanced.py</div>
                    <div className="text-green-400">✓ pass3_merge.py</div>
                    <div className="text-green-400">✓ pass4_zon_bridge.py</div>
                    <div className="text-green-400">✓ lore_to_zon.py</div>
                  </div>
                </div>
                <div className="space-y-2">
                  <h3 className="font-semibold text-purple-400">Output Formats</h3>
                  <div className="text-sm space-y-1">
                    <div><span className="text-cyan-400">out_pass1_*.txt</span> - Semantic structure</div>
                    <div><span className="text-cyan-400">out_pass2_*.metta</span> - Inference atoms</div>
                    <div><span className="text-cyan-400">zonj_*.json</span> - Merged scene data</div>
                    <div><span className="text-cyan-400">*.zon</span> - Human-readable ZON</div>
                    <div><span className="text-cyan-400">*.zonj.json</span> - Canonical ZON JSON</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Pipeline Tab */}
        {activeTab === 'pipeline' && (
          <div className="space-y-4">
            {pipelineStages.map((stage, idx) => (
              <div
                key={stage.id}
                className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => setExpandedStage(expandedStage === stage.id ? null : stage.id)}
                  className="w-full p-6 flex items-start justify-between hover:bg-slate-800/70 transition-all"
                >
                  <div className="flex items-start gap-4">
                    <div className="bg-cyan-500/20 p-3 rounded-lg">
                      {idx === 0 && <FileText className="w-6 h-6 text-cyan-400" />}
                      {idx === 1 && <Zap className="w-6 h-6 text-cyan-400" />}
                      {idx === 2 && <GitBranch className="w-6 h-6 text-cyan-400" />}
                      {idx === 3 && <Database className="w-6 h-6 text-cyan-400" />}
                      {idx === 4 && <FileText className="w-6 h-6 text-cyan-400" />}
                    </div>
                    <div className="text-left">
                      <h3 className="text-xl font-bold text-cyan-400">{stage.name}</h3>
                      <p className="text-sm text-slate-400 mt-1">{stage.file}</p>
                      <p className="text-sm text-slate-300 mt-2">{stage.description}</p>
                    </div>
                  </div>
                  <div className="text-slate-500">
                    {expandedStage === stage.id ? '▼' : '▶'}
                  </div>
                </button>

                {expandedStage === stage.id && (
                  <div className="px-6 pb-6 space-y-4">
                    <div className="grid md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="text-sm font-semibold text-purple-400 mb-2">Input</h4>
                        <div className="bg-slate-900/50 p-3 rounded text-sm text-slate-300">
                          {stage.input}
                        </div>
                      </div>
                      <div>
                        <h4 className="text-sm font-semibold text-purple-400 mb-2">Output</h4>
                        <div className="bg-slate-900/50 p-3 rounded text-sm text-slate-300">
                          {stage.output}
                        </div>
                      </div>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-purple-400 mb-2">Features</h4>
                      <ul className="space-y-1">
                        {stage.features.map((feature, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                            <CheckCircle className="w-4 h-4 text-green-500 mt-0.5 flex-shrink-0" />
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 className="text-sm font-semibold text-purple-400 mb-2">Example Output</h4>
                      <pre className="bg-slate-950 p-4 rounded text-xs text-green-400 overflow-x-auto">
                        {stage.exampleOutput}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Architecture Tab */}
        {activeTab === 'architecture' && (
          <div className="space-y-6">
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-cyan-400 mb-4">Philosophy</h2>
              <ul className="space-y-2">
                {architectureNotes.philosophy.map((item, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full mt-2 flex-shrink-0"></div>
                    <span className="text-slate-300">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-cyan-400 mb-4">Core Technologies</h2>
              <div className="grid md:grid-cols-2 gap-4">
                {architectureNotes.core_tech.map((tech, i) => (
                  <div key={i} className="bg-slate-900/50 p-4 rounded border-l-4 border-cyan-500">
                    <p className="text-slate-300">{tech}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-cyan-400 mb-4">Data Flow</h2>
              <div className="space-y-3">
                {architectureNotes.workflow.map((step, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <div className="bg-purple-500/20 text-purple-400 px-3 py-1 rounded font-bold text-sm">
                      {i + 1}
                    </div>
                    <p className="text-slate-300 flex-1">{step}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Troubleshoot Tab */}
        {activeTab === 'troubleshoot' && (
          <div className="space-y-4">
            <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-cyan-400 mb-4">Common Issues & Solutions</h2>
              <div className="space-y-4">
                {commonIssues.map((item, i) => (
                  <div key={i} className="bg-slate-900/50 border-l-4 border-yellow-500 p-4 rounded">
                    <div className="flex items-start gap-3">
                      <AlertCircle className="w-5 h-5 text-yellow-500 mt-0.5 flex-shrink-0" />
                      <div className="flex-1">
                        <h3 className="font-bold text-yellow-400 mb-2">{item.issue}</h3>
                        <p className="text-slate-300 text-sm mb-2">{item.solution}</p>
                        <code className="text-xs text-slate-500">{item.file}</code>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-slate-800/50 backdrop-blur border border-slate-700 rounded-lg p-6">
              <h2 className="text-2xl font-bold text-cyan-400 mb-4">Debugging Tips</h2>
              <div className="space-y-3 text-sm">
                <div className="bg-slate-900/50 p-3 rounded">
                  <h3 className="text-purple-400 font-semibold mb-1">Check intermediate outputs</h3>
                  <p className="text-slate-300">
                    Each pass creates debug-friendly output - inspect out_pass1_*.txt to verify semantic structure before proceeding
                  </p>
                </div>
                <div className="bg-slate-900/50 p-3 rounded">
                  <h3 className="text-purple-400 font-semibold mb-1">Validate ZONJ structure</h3>
                  <p className="text-slate-300">
                    Use <code className="bg-slate-950 px-2 py-0.5 rounded">python3 -m json.tool zonj_*.json</code> to pretty-print and validate JSON
                  </p>
                </div>
                <div className="bg-slate-900/50 p-3 rounded">
                  <h3 className="text-purple-400 font-semibold mb-1">Test with small samples first</h3>
                  <p className="text-slate-300">
                    Start with 5-10 line narratives to verify the pipeline before processing large documents
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 pt-6 border-t border-slate-700 text-center text-slate-500 text-sm">
          <p>EngAIn • World Model as Truth • ZW → ZON4D Memory Fabric</p>
          <p className="mt-1">Philosophy: AI Logic Built for AI, Not Humans</p>
        </div>
      </div>
    </div>
  );
}
