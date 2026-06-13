"""Safe AP rule predicate and decision-effect evaluator.

This module evaluates already-loaded ``ap/0.1`` rule dictionaries only. It does
not parse ZON, import authority_gate, orchestrate authority decisions, or mutate
runtime/world/entity state.

Boundary note:
classification owns tier derivation; evaluator owns predicate truth;
authority_gate owns orchestration. In particular, FINALIZED policy derivation
must remain upstream of this module.
"""

from __future__ import annotations

import ast
import copy
import re
from typing import Any, Dict, List, Tuple

_ALLOWED_PATHS = {
    "envelope.reality_mode",
    "envelope.actor_authority_tier",
    "action.required_tier",
}
_ALLOWED_EFFECT_FIELDS = {"allowed", "blocked_by", "reason"}
_EFFECT_RE = re.compile(r"^decision\.([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$")

_DEFAULT_DECISION: Dict[str, Any] = {
    "allowed": None,
    "blocked_by": None,
    "reason": None,
    "errors": [],
}


def predicates_pass(rule: dict, envelope: dict, action: dict) -> bool:
    """
    Return True only if every requires line evaluates true.
    Empty requires list returns True.
    Invalid/unsupported predicate returns False.
    """
    passed, _errors = _evaluate_predicates(rule, envelope, action)
    return passed


def apply_decision_effects(rule: dict, decision: dict) -> dict:
    """
    Apply allowed decision.* effects to a copy of decision and return it.

    Only decision.allowed, decision.blocked_by, and decision.reason may be
    written. Unsupported effects are recorded in decision["errors"] and ignored.
    """
    next_decision = _copy_decision(decision)

    for effect in rule.get("effects", []) or []:
        if not isinstance(effect, str):
            _append_error(
                next_decision,
                "unsupported_effect",
                "Effect must be a string",
                effect,
            )
            continue

        parsed = _parse_effect(effect)
        if parsed["error"] is not None:
            _append_error(
                next_decision,
                "unsupported_effect",
                parsed["error"],
                effect,
            )
            continue

        field = parsed["field"]
        value = parsed["value"]
        if field == "allowed" and not isinstance(value, bool):
            _append_error(
                next_decision,
                "unsupported_effect",
                "decision.allowed only accepts true or false",
                effect,
            )
            continue
        if field in {"blocked_by", "reason"} and not isinstance(value, str):
            _append_error(
                next_decision,
                "unsupported_effect",
                f"decision.{field} only accepts string literals",
                effect,
            )
            continue

        next_decision[field] = value

    return next_decision


def evaluate_rule(
    rule: dict,
    envelope: dict,
    action: dict,
    decision: dict | None = None,
) -> dict:
    """
    Evaluate one loaded AP rule against normalized envelope/action inputs.

    Returns a plain dict with rule_id, predicate_passed, decision, and errors.
    """
    current_decision = _copy_decision(decision or _DEFAULT_DECISION)
    predicate_passed, predicate_errors = _evaluate_predicates(rule, envelope, action)

    for error in predicate_errors:
        _append_error(
            current_decision,
            error["code"],
            error["message"],
            error.get("source"),
        )

    if predicate_passed:
        current_decision = apply_decision_effects(rule, current_decision)

    return {
        "rule_id": rule.get("id"),
        "predicate_passed": predicate_passed,
        "decision": current_decision,
        "errors": list(current_decision.get("errors", [])),
    }


def _evaluate_predicates(
    rule: dict,
    envelope: dict,
    action: dict,
) -> Tuple[bool, List[Dict[str, Any]]]:
    errors: List[Dict[str, Any]] = []
    for predicate in rule.get("requires", []) or []:
        passed, error = _evaluate_predicate(predicate, envelope, action)
        if error is not None:
            errors.append(error)
            return False, errors
        if not passed:
            return False, errors
    return True, errors


def _evaluate_predicate(
    predicate: Any,
    envelope: dict,
    action: dict,
) -> Tuple[bool, Dict[str, Any] | None]:
    if not isinstance(predicate, str):
        return False, _predicate_error("Predicate must be a string", predicate)

    try:
        tree = ast.parse(predicate, mode="eval")
    except SyntaxError:
        return False, _predicate_error("Predicate syntax is unsupported", predicate)

    try:
        value = _eval_predicate_node(tree.body, envelope, action)
    except _UnsupportedPredicate as exc:
        return False, _predicate_error(str(exc), predicate)

    if not isinstance(value, bool):
        return False, _predicate_error("Predicate did not evaluate to bool", predicate)
    return value, None


def _eval_predicate_node(node: ast.AST, envelope: dict, action: dict) -> Any:
    if isinstance(node, ast.BoolOp):
        if not isinstance(node.op, ast.And):
            raise _UnsupportedPredicate("Only inline 'and' boolean predicates are supported")
        for value in node.values:
            evaluated = _eval_predicate_node(value, envelope, action)
            if not isinstance(evaluated, bool):
                raise _UnsupportedPredicate("Inline 'and' operands must be boolean predicates")
            if evaluated is False:
                return False
        return True

    if isinstance(node, ast.Compare):
        return _eval_compare(node, envelope, action)

    return _literal_or_path_value(node, envelope, action)


def _eval_compare(node: ast.Compare, envelope: dict, action: dict) -> bool:
    left = _literal_or_path_value(node.left, envelope, action)
    for operator, comparator in zip(node.ops, node.comparators):
        right = _literal_or_path_value(comparator, envelope, action)
        try:
            if not _compare_values(left, operator, right):
                return False
        except TypeError as exc:
            raise _UnsupportedPredicate("Comparison operands are incompatible") from exc
        left = right
    return True


def _compare_values(left: Any, operator: ast.cmpop, right: Any) -> bool:
    if isinstance(operator, ast.Eq):
        return left == right
    if isinstance(operator, ast.NotEq):
        return left != right
    if isinstance(operator, ast.Gt):
        return left > right
    if isinstance(operator, ast.GtE):
        return left >= right
    if isinstance(operator, ast.Lt):
        return left < right
    if isinstance(operator, ast.LtE):
        return left <= right
    if isinstance(operator, ast.In):
        if not isinstance(right, list):
            raise _UnsupportedPredicate("Right side of 'in' must be a list literal")
        return left in right
    raise _UnsupportedPredicate("Comparison operator is unsupported")


def _literal_or_path_value(node: ast.AST, envelope: dict, action: dict) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (str, int, float)):
            return node.value
        raise _UnsupportedPredicate("Only string, int, and float literals are supported")

    if isinstance(node, ast.List):
        return [_literal_or_path_value(item, envelope, action) for item in node.elts]

    if isinstance(node, ast.Attribute):
        path = _attribute_path(node)
        if path not in _ALLOWED_PATHS:
            raise _UnsupportedPredicate(f"Dotted path is not allowed: {path}")
        root, key = path.split(".", 1)
        source = envelope if root == "envelope" else action
        if key not in source:
            raise _UnsupportedPredicate(f"Dotted path is missing: {path}")
        return source[key]

    if isinstance(node, ast.Name):
        raise _UnsupportedPredicate(f"Bare name is not allowed: {node.id}")

    raise _UnsupportedPredicate(f"Unsupported predicate syntax: {type(node).__name__}")


def _attribute_path(node: ast.Attribute) -> str:
    parts: List[str] = []
    current: ast.AST = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        raise _UnsupportedPredicate("Only dotted paths are supported")
    parts.append(current.id)
    parts.reverse()
    return ".".join(parts)


def _parse_effect(effect: str) -> Dict[str, Any]:
    match = _EFFECT_RE.match(effect.strip())
    if match is None:
        return {"field": None, "value": None, "error": "Only decision.* assignment effects are supported"}

    field, raw_value = match.groups()
    if field not in _ALLOWED_EFFECT_FIELDS:
        return {"field": field, "value": None, "error": f"decision.{field} writes are not allowed"}

    if any(token in effect for token in ("+=", "-=", "*=", "/=")):
        return {"field": field, "value": None, "error": "Augmented assignment effects are not allowed"}

    parsed_value = _parse_effect_value(raw_value.strip())
    if parsed_value["error"] is not None:
        return {"field": field, "value": None, "error": parsed_value["error"]}

    return {"field": field, "value": parsed_value["value"], "error": None}


def _parse_effect_value(raw_value: str) -> Dict[str, Any]:
    if raw_value == "true":
        return {"value": True, "error": None}
    if raw_value == "false":
        return {"value": False, "error": None}
    if len(raw_value) >= 2 and raw_value[0] == '"' and raw_value[-1] == '"':
        try:
            value = ast.literal_eval(raw_value)
        except (SyntaxError, ValueError):
            return {"value": None, "error": "String literal is invalid"}
        if isinstance(value, str):
            return {"value": value, "error": None}
    return {"value": None, "error": "Only lowercase booleans and string literals are supported"}


def _copy_decision(decision: dict) -> dict:
    copied = copy.deepcopy(decision)
    for key, value in _DEFAULT_DECISION.items():
        if key not in copied:
            copied[key] = copy.deepcopy(value)
    if not isinstance(copied.get("errors"), list):
        copied["errors"] = []
    return copied


def _append_error(decision: dict, code: str, message: str, source: Any = None) -> None:
    decision.setdefault("errors", []).append(
        {
            "code": code,
            "message": message,
            "source": source,
        }
    )


def _predicate_error(message: str, source: Any) -> Dict[str, Any]:
    return {
        "code": "unsupported_predicate",
        "message": message,
        "source": source,
    }


class _UnsupportedPredicate(ValueError):
    """Raised internally when a predicate is outside the safe grammar."""
