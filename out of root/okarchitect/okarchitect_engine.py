
okarchitect_engine.py – v1.0 “Deep-Mr Council”

"""
OKArchitectEngine v1.0
Deep-Mr Council Fusion
----------------------

Logical agents:
  - listener   : parses raw user prompt → TaskSpec
  - dispatcher : builds ExecutionPlan (routing)
  - reasoner   : analysis, decomposition, troubleshooting
  - designer   : blueprints / architecture
  - producer   : implementation / code / artifacts

You must wire actual LLM calls into `call_model()` or per-agent
`_llm()` methods. Everything else is ready to integrate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
import textwrap


# ============================================================
# Core data models
# ============================================================

@dataclass
class TaskSpec:
    raw_input: str
    intent: str = "unknown"      # e.g. code_small, debugging, kernel_update, narrative_prose
    domain: str = "unknown"      # e.g. EngAIn_kernel, Godot_ZW, narrative_lore
    complexity: str = "unknown"  # low | medium | high
    risk_level: str = "low"      # low | medium | high
    constraints: List[str] = field(default_factory=list)
    artifacts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionPlan:
    route: List[str]              # e.g. ["reasoner", "designer", "producer"]
    strategy: str = "single_pass" # single_pass | iterative_refine
    max_steps: int = 3
    require_review: bool = False
    notes: List[str] = field(default_factory=list)


@dataclass
class AgentResult:
    role: str
    content: Any
    meta: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# LLM plumbing hook (you wire this)
# ============================================================

LLMFn = Callable[[str, str], str]
# signature: llm_fn(model_name: str, prompt: str) -> str


def default_llm_stub(model_name: str, prompt: str) -> str:
    """
    Placeholder. Replace with real call to Ollama/OpenRouter/etc.
    """
    raise NotImplementedError(
        f"LLM backend not wired. Tried to call model '{model_name}'.\n"
        "Pass a callable to OKArchitectEngine(llm_backend=...)"
    )


# ============================================================
# Base Agent
# ============================================================

class Agent:
    def __init__(self, role: str, model_name: str, llm_backend: LLMFn):
        self.role = role
        self.model_name = model_name
        self.llm = llm_backend

    def run(self, task: TaskSpec, context: Dict[str, Any]) -> AgentResult:
        raise NotImplementedError


# ============================================================
# Listener – EngAIn-aware intent/domain classifier
# ============================================================

class ListenerAgent(Agent):
    """
    Turns raw user text into TaskSpec:
      - detects intent
      - classifies domain
      - estimates complexity/risk
      - extracts simple constraints
    """

    def run(self, task: TaskSpec, context: Dict[str, Any]) -> AgentResult:
        text = task.raw_input.lower()

        intent = "qna_simple"
        domain = "general"
        risk = "low"

        # Very simple keyword heuristics — you can later replace this
        # with an LLM-based classifier using self.llm(...)
        if any(k in text for k in ["kernel", "apsim", "ap kernel", "zon4d"]):
            domain = "EngAIn_kernel"
            intent = "kernel_update"
            risk = "high"
        elif any(k in text for k in ["godot", "gscript", "gds", "node", "scene"]):
            domain = "Godot_ZW"
            intent = "code_small"
        elif any(k in text for k in ["refactor", "rewrite", "cleanup"]):
            intent = "refactor_large_module"
            domain = "EngAIn_kernel"
        elif any(k in text for k in ["plan", "roadmap", "design", "architecture"]):
            intent = "architecture"
        elif any(k in text for k in ["debug", "fix", "bug", "error", "traceback"]):
            intent = "debugging"
        elif any(k in text for k in ["scene", "dialogue", "dialog", "chapter", "lore"]):
            domain = "narrative_lore"
            if "structure" in text or "beats" in text:
                intent = "narrative_structural"
            else:
                intent = "narrative_prose"

        if intent in {"qna_simple", "code_small"}:
            complexity = "low"
        elif intent in {"refactor_large_module", "architecture"}:
            complexity = "high"
        elif intent in {"kernel_update"}:
            complexity = "high"
        else:
            complexity = "medium"

        # Very naive constraint extraction
        constraints: List[str] = []
        if "no new deps" in text or "no new dependencies" in text:
            constraints.append("no_new_dependencies")
        if "keep api" in text or "backwards compatible" in text:
            constraints.append("backwards_compatible")
        if "diff only" in text or "patch only" in text:
            constraints.append("diff_only")

        spec = TaskSpec(
            raw_input=task.raw_input,
            intent=intent,
            domain=domain,
            complexity=complexity,
            risk_level=risk,
            constraints=constraints,
            artifacts=task.artifacts.copy(),
        )

        return AgentResult(role=self.role, content=spec)


# ============================================================
# Reasoner – analysis + troubleshooting
# ============================================================

class ReasonerAgent(Agent):
    """
    - For normal flow: decomposes task, finds invariants, dependencies.
    - For troubleshooting: called again with extra context when a gate fails.
    """

    def run(self, task: TaskSpec, context: Dict[str, Any]) -> AgentResult:
        # default to "analysis" mode
        return self._analyze(task, context)

    def _analyze(self, task: TaskSpec, context: Dict[str, Any]) -> AgentResult:
        prompt = textwrap.dedent(f"""
        You are the REASONER in a multi-agent architecture for a game engine + narrative system.

        Task intent: {task.intent}
        Domain: {task.domain}
        Complexity: {task.complexity}
        Risk level: {task.risk_level}
        Constraints: {task.constraints}

        Raw user request:
        {task.raw_input}

        Your job:
        - Decompose this into clear steps.
        - Identify any invariants that must NOT be broken.
        - Identify affected modules / files in a system like EngAIn/ZON4D/Godot-ZW.
        - Note any obvious risks.

        Respond in JSON with keys:
        - steps: [string]
        - invariants: [string]
        - affected_areas: [string]
        - risks: [string]
        """).strip()

        # You can uncomment this and parse actual JSON once you wire LLM
        # raw = self.llm(self.model_name, prompt)
        # plan = json.loads(raw)

        # Stub plan (safe fallback)
        plan = {
            "steps": [
                "Clarify current behavior and desired change.",
                "Identify all modules/files that implement this behavior.",
                "Define invariants that must not change.",
                "Propose safe modification strategy.",
            ],
            "invariants": [
                "Engine global contract must remain valid.",
                "Save/load formats must not silently break.",
            ],
            "affected_areas": [
                "kernel core loop",
                "AP rules and adapters",
            ],
            "risks": [
                "Silent state corruption if invariants are broken.",
            ],
        }

        return AgentResult(
            role=self.role,
            content=plan,
            meta={"mode": "analysis"},
        )

    def troubleshoot(self, task: TaskSpec, context: Dict[str, Any], failed_role: str) -> AgentResult:
        """
        Called when a quality gate fails, to refine plan or suggest corrections.
        """
        prompt = textwrap.dedent(f"""
        You are the REASONER in a multi-agent system.

        A quality gate FAILED for role: {failed_role}

        Task:
        intent={task.intent}, domain={task.domain}, risk={task.risk_level}
        raw_input:
        {task.raw_input}

        Context so far (summarized, not raw code):
        {self._summarize_context(context)}

        Your job:
        - Diagnose why the {failed_role} output might be weak or incorrect.
        - Suggest corrections or an updated plan.
        - Indicate whether to rerun {failed_role} or change the route.

        Respond in JSON with keys:
        - diagnosis: [string]
        - updated_steps: [string]
        - rerun_roles: [string]  # e.g. ["designer", "producer"]
        """).strip()

        # raw = self.llm(self.model_name, prompt)
        # result = json.loads(raw)

        result = {
            "diagnosis": [f"{failed_role} output failed a basic structural check (stub)."],
            "updated_steps": ["Revisit design and ensure modules/APIs are coherent."],
            "rerun_roles": [failed_role],
        }

        return AgentResult(
            role=self.role,
            content=result,
            meta={"mode": "troubleshoot", "failed_role": failed_role},
        )

    @staticmethod
    def _summarize_context(context: Dict[str, Any]) -> str:
        keys = list(context.keys())
        return f"Context keys: {keys}"


# ============================================================
# Designer – blueprint / architecture
# ============================================================

class DesignerAgent(Agent):
    def run(self, task: TaskSpec, context: Dict[str, Any]) -> AgentResult:
        reasoning = context.get("reasoner", {})
        prompt = textwrap.dedent(f"""
        You are the DESIGNER/ARCHITECT for a multi-agent game engine (EngAIn/ZON4D/Godot-ZW).

        Task intent: {task.intent}
        Domain: {task.domain}
        Constraints: {task.constraints}

        Reasoner plan:
        {reasoning}

        Design a high-level blueprint:
        - Modules/files to create or modify.
        - Key functions/classes.
        - Data structures.
        - How this fits into existing EngAIn/ZON4D/AP/Godot layers.

        Respond in JSON with keys:
        - modules: [string]          # filenames or logical modules
        - apis: [string]             # function/class signatures
        - data_structures: [string]
        - notes: [string]
        """).strip()

        # raw = self.llm(self.model_name, prompt)
        # design = json.loads(raw)

        # Stub design
        design = {
            "modules": ["kernel/tasks.py", "kernel/router.py"],
            "apis": ["def schedule_task(...)", "class TaskRouter(...)"],
            "data_structures": ["TaskSpec", "ExecutionPlan"],
            "notes": ["Stub design; replace with LLM-driven JSON later."],
        }

        return AgentResult(role=self.role, content=design)


# ============================================================
# Producer – implementation engine
# ============================================================

class ProducerAgent(Agent):
    def run(self, task: TaskSpec, context: Dict[str, Any]) -> AgentResult:
        reasoning = context.get("reasoner")
        design = context.get("designer")

        prompt = textwrap.dedent(f"""
        You are the PRODUCER/CODER.

        Implement the requested change or feature for this task:

        Task intent: {task.intent}
        Domain: {task.domain}
        Constraints: {task.constraints}

        Reasoner plan:
        {reasoning}

        Designer blueprint:
        {design}

        Rules:
        - Generate code that fits the described architecture.
        - Respect invariants and constraints.
        - Prefer diffs/patch-style output if modifying existing files.
        - Keep it minimal but correct.

        Respond with:
        - A short explanation at top as comments.
        - Then the code.
        """)

        # raw = self.llm(self.model_name, prompt)
        # For now we stub a placeholder
        code = textwrap.dedent("""
        # TODO: Implement real code via Producer LLM
        # This is a placeholder generated by the council skeleton.

        def placeholder():
            \"\"\"Replace this with real implementation.\"\"\"
            return "ok"
        """).lstrip()

        return AgentResult(role=self.role, content={"code": code})


# ============================================================
# Dispatcher – routing brain
# ============================================================

class DispatcherAgent(Agent):
    """
    Decides which agents to invoke for a given TaskSpec.
    """

    def run(self, task: TaskSpec, context: Dict[str, Any]) -> AgentResult:
        plan = self.route_task(task)
        return AgentResult(role=self.role, content=plan)

    def route_task(self, task: TaskSpec) -> ExecutionPlan:
        intent = task.intent
        complexity = task.complexity

        # Fused routing from Deep + Mr + Verdict
        if intent in {"qna_simple"}:
            route = ["producer"]

        elif intent in {"code_small"} and complexity == "low":
            route = ["producer"]

        elif intent == "debugging":
            route = ["reasoner", "producer"]

        elif intent == "planning":
            route = ["reasoner", "designer"]

        elif intent == "architecture":
            route = ["reasoner", "designer", "producer"]

        elif intent == "kernel_update":
            route = ["reasoner", "designer", "producer"]

        elif intent == "narrative_structural":
            route = ["designer", "producer"]

        elif intent == "narrative_prose":
            route = ["designer"]

        elif intent == "refactor_large_module":
            route = ["reasoner", "producer"]

        else:
            # unknown? err on the side of thinking first
            route = ["reasoner", "producer"]

        require_review = (intent == "kernel_update")

        strategy = "single_pass" if complexity == "low" else "iterative_refine"

        return ExecutionPlan(
            route=route,
            strategy=strategy,
            max_steps=3,
            require_review=require_review,
            notes=[],
        )


# ============================================================
# Orchestrator – OKArchitectEngine
# ============================================================

class OKArchitectEngine:
    """
    High-level orchestrator.
    You construct this once, then call engine.handle_user_input(text).
    """

    def __init__(
        self,
        llm_backend: LLMFn = default_llm_stub,
        listener_model: str = "phi3-mini",
        dispatcher_model: str = "phi3-mini",
        reasoner_model: str = "dolphin-llama3",
        designer_model: str = "deep-coder-architect",
        producer_model: str = "deep-coder-impl",
    ):
        self.llm = llm_backend

        self.listener = ListenerAgent("listener", listener_model, self.llm)
        self.dispatcher = DispatcherAgent("dispatcher", dispatcher_model, self.llm)
        self.reasoner = ReasonerAgent("reasoner", reasoner_model, self.llm)
        self.designer = DesignerAgent("designer", designer_model, self.llm)
        self.producer = ProducerAgent("producer", producer_model, self.llm)

    # ---------- Public entrypoint ----------

    def handle_user_input(self, text: str) -> Dict[str, Any]:
        """
        Full council run for a single user request.
        Returns a dict with final result + trace.
        """
        context: Dict[str, Any] = {"agent_trace": []}

        # Step 1: Listener → TaskSpec
        initial_task = TaskSpec(raw_input=text)
        listener_res = self.listener.run(initial_task, context)
        task_spec: TaskSpec = listener_res.content
        self._trace(context, listener_res)

        # Step 2: Dispatcher → ExecutionPlan
        dispatcher_res = self.dispatcher.run(task_spec, context)
        plan: ExecutionPlan = dispatcher_res.content
        self._trace(context, dispatcher_res)

        # Step 3: Execute route with quality gates + self-heal
        for role in plan.route:
            res = self._run_role(role, task_spec, context)
            if res is None:
                # unknown role; skip
                continue
            self._trace(context, res)

            if not self._quality_gate(role, task_spec, context):
                # quality failed → send to Reasoner for troubleshooting
                fix_res = self.reasoner.troubleshoot(task_spec, context, failed_role=role)
                self._trace(context, fix_res)
                fix = fix_res.content
                rerun_roles = fix.get("rerun_roles", [])
                # naive: rerun the failed role once with updated context
                if role in rerun_roles:
                    res = self._run_role(role, task_spec, context)
                    if res:
                        self._trace(context, res)

        # Step 4: Final output
        final = self._build_final_output(task_spec, context, plan)
        return final

    # ---------- Internals ----------

    def _run_role(
        self,
        role: str,
        task_spec: TaskSpec,
        context: Dict[str, Any],
    ) -> Optional[AgentResult]:
        if role == "reasoner":
            res = self.reasoner.run(task_spec, context)
        elif role == "designer":
            res = self.designer.run(task_spec, context)
        elif role == "producer":
            res = self.producer.run(task_spec, context)
        else:
            return None

        # store content under role key
        context[role] = res.content
        return res

    def _quality_gate(self, role: str, task: TaskSpec, context: Dict[str, Any]) -> bool:
        """
        Simple structural checks for each role.
        Replace/extend with real logic as needed.
        """
        if role == "reasoner":
            plan = context.get("reasoner", {})
            steps = plan.get("steps") if isinstance(plan, dict) else None
            return bool(steps)

        if role == "designer":
            design = context.get("designer", {})
            modules = design.get("modules") if isinstance(design, dict) else None
            return bool(modules)

        if role == "producer":
            prod = context.get("producer", {})
            code = prod.get("code") if isinstance(prod, dict) else None
            return isinstance(code, str) and len(code.strip()) > 0

        # default: pass
        return True

    @staticmethod
    def _trace(context: Dict[str, Any], result: AgentResult) -> None:
        trace = context.setdefault("agent_trace", [])
        trace.append(
            {
                "role": result.role,
                "meta": result.meta,
            }
        )

    @staticmethod
    def _build_final_output(
        task: TaskSpec,
        context: Dict[str, Any],
        plan: ExecutionPlan,
    ) -> Dict[str, Any]:
        producer_out = context.get("producer")
        explanation = None
        code = None

        if isinstance(producer_out, dict):
            code = producer_out.get("code")
        else:
            explanation = str(producer_out)

        return {
            "task": {
                "intent": task.intent,
                "domain": task.domain,
                "complexity": task.complexity,
                "risk_level": task.risk_level,
                "constraints": task.constraints,
            },
            "plan": {
                "route": plan.route,
                "strategy": plan.strategy,
                "require_review": plan.require_review,
            },
            "result": {
                "explanation": explanation,
                "code": code,
            },
            "trace": context.get("agent_trace", []),
        }


# ============================================================
# Minimal manual test (remove if you wire into larger system)
# ============================================================

if __name__ == "__main__":
    # smoke-test with stub backend, will raise NotImplementedError
    engine = OKArchitectEngine()
    try:
        out = engine.handle_user_input(
            "Update the EngAIn kernel so tasks can be batched per tick without "
            "breaking the global AP contract. Keep it backwards compatible and "
            "prefer diff only."
        )
        print(out)
    except NotImplementedError as e:
        print("LLM backend not wired yet. Skeleton is ready.")
        print(e)

