from __future__ import annotations

from functools import lru_cache
from math import log1p, prod

import numpy as np
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor, IsolationForest
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from .models import Scenario

RANDOM_STATE = 59
MODEL_VERSION = "0.2.0"
FEATURE_SCHEMA_VERSION = "2026-08-17"

ROUTER_CLASSES = {
    0: "compact-model",
    1: "reasoning-model",
    2: "high-reliability-model",
}

ROUTER_TASKS = {
    "extract": 0,
    "retrieve": 1,
    "investigate": 2,
    "summarize": 3,
    "high_impact_proposal": 4,
}

ROUTER_FEATURES = [
    "task_code",
    "complexity",
    "evidence_count",
    "graph_depth",
    "risk",
    "latency_budget_ms",
    "cost_budget",
    "approval_required",
]

CONTROL_FEATURES = [
    "edge_risk",
    "path_length",
    "position_ratio",
    "downstream_edges",
    "original_path_risk",
    "control_code",
]

WORKFLOW_FEATURES = [
    "step_count",
    "policy_checks",
    "denied_tools",
    "errors",
    "agent_transitions",
    "repeated_steps",
    "approval_signals",
    "agent_imbalance",
    "log_total_latency_ms",
]

CONTROL_CODES = {
    "phishing-resistant MFA": 0,
    "token protection": 1,
    "continuous access evaluation": 2,
    "least-privilege OAuth scopes": 3,
    "admin consent workflow": 4,
    "scope reduction": 5,
    "privileged access workstation": 6,
    "just-in-time privilege": 7,
}


def _path_risk_from_values(risks: np.ndarray) -> float:
    return float(1.0 - prod(1.0 - float(np.clip(value, 0.0, 1.0)) for value in risks))


def _router_dataset(n: int = 1200) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(RANDOM_STATE)
    rows: list[list[float]] = []
    labels: list[int] = []

    for _ in range(n):
        task_code = int(rng.integers(0, 5))
        complexity = float(rng.uniform(0.05, 1.0))
        evidence_count = int(rng.integers(0, 30))
        graph_depth = int(rng.integers(1, 10))
        risk = float(rng.uniform(0.02, 0.98))
        latency_budget_ms = float(rng.uniform(150, 2500))
        cost_budget = float(rng.uniform(0.002, 0.12))
        approval_required = int(rng.random() < 0.12)

        if approval_required or task_code == 4 or risk >= 0.86:
            label = 2
        elif task_code == 2 or complexity >= 0.58 or graph_depth >= 6 or evidence_count >= 16:
            label = 1
        elif latency_budget_ms <= 450 or cost_budget <= 0.018:
            label = 0
        else:
            label = 1 if risk >= 0.55 else 0

        rows.append([
            task_code,
            complexity,
            evidence_count,
            graph_depth,
            risk,
            latency_budget_ms,
            cost_budget,
            approval_required,
        ])
        labels.append(label)

    return np.asarray(rows, dtype=float), np.asarray(labels, dtype=int)


@lru_cache(maxsize=1)
def router_model() -> tuple[GradientBoostingClassifier, dict[str, float]]:
    x, y = _router_dataset()
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    model = GradientBoostingClassifier(random_state=RANDOM_STATE)
    model.fit(x_train, y_train)
    pred = model.predict(x_test)
    return model, {
        "synthetic_holdout_accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "training_rows": int(len(x_train)),
        "holdout_rows": int(len(x_test)),
    }


def recommend_model(task: str, context: dict | None = None) -> dict:
    context = dict(context or {})
    task_code = ROUTER_TASKS.get(task, 2)
    row = np.asarray([[
        task_code,
        float(context.get("complexity", 0.5)),
        int(context.get("evidence_count", 0)),
        int(context.get("graph_depth", 1)),
        float(context.get("risk", 0.5)),
        float(context.get("latency_budget_ms", 1200)),
        float(context.get("cost_budget", 0.05)),
        int(bool(context.get("approval_required", False))),
    ]], dtype=float)

    model, metrics = router_model()
    predicted = int(model.predict(row)[0])
    probabilities = model.predict_proba(row)[0]
    ml_class = ROUTER_CLASSES[predicted]

    safety_override = bool(context.get("approval_required", False)) or task == "high_impact_proposal"
    selected = "high-reliability-model" if safety_override else ml_class

    return {
        "task": task,
        "model": "GradientBoostingClassifier",
        "model_version": MODEL_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "ml_model_class": ml_class,
        "selected_model_class": selected,
        "confidence": round(float(max(probabilities)), 4),
        "safety_override": safety_override,
        "external_call": False,
        "evaluation": metrics,
        "boundary": "synthetic routing benchmark; safety overrides remain deterministic",
    }


def _control_dataset(n: int = 1800) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(RANDOM_STATE + 1)
    rows: list[list[float]] = []
    targets: list[float] = []

    for _ in range(n):
        length = int(rng.integers(2, 7))
        risks = rng.uniform(0.08, 0.88, size=length)
        idx = int(rng.integers(0, length))
        original = _path_risk_from_values(risks)
        hardened = risks.copy()
        hardened[idx] = hardened[idx] * 0.35
        residual = _path_risk_from_values(hardened)
        reduction = original - residual
        position_ratio = idx / max(1, length - 1)
        control_code = int(rng.integers(0, len(CONTROL_CODES)))

        rows.append([
            float(risks[idx]),
            length,
            position_ratio,
            length - idx - 1,
            original,
            control_code,
        ])
        targets.append(reduction)

    return np.asarray(rows, dtype=float), np.asarray(targets, dtype=float)


@lru_cache(maxsize=1)
def control_model() -> tuple[GradientBoostingRegressor, dict[str, float]]:
    x, y = _control_dataset()
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.25,
        random_state=RANDOM_STATE,
    )
    model = GradientBoostingRegressor(random_state=RANDOM_STATE)
    model.fit(x_train, y_train)
    pred = model.predict(x_test)
    return model, {
        "synthetic_holdout_mae": round(float(mean_absolute_error(y_test, pred)), 5),
        "synthetic_holdout_r2": round(float(r2_score(y_test, pred)), 4),
        "training_rows": int(len(x_train)),
        "holdout_rows": int(len(x_test)),
    }


def rank_controls(scenario: Scenario, original_risk: float) -> dict:
    model, metrics = control_model()
    rows = []
    candidates = []
    length = len(scenario.path)

    for idx, edge in enumerate(scenario.path):
        control_code = CONTROL_CODES.get(edge.control, len(CONTROL_CODES))
        rows.append([
            edge.risk,
            length,
            idx / max(1, length - 1),
            length - idx - 1,
            original_risk,
            control_code,
        ])
        candidates.append({
            "edge_index": idx,
            "control": edge.control,
            "source": edge.source,
            "target": edge.target,
        })

    predictions = model.predict(np.asarray(rows, dtype=float)) if rows else np.asarray([])
    for candidate, prediction in zip(candidates, predictions):
        candidate["predicted_risk_reduction"] = round(max(0.0, float(prediction)), 4)

    candidates.sort(key=lambda item: (-item["predicted_risk_reduction"], item["control"]))
    return {
        "model": "GradientBoostingRegressor",
        "model_version": MODEL_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "ranked_candidates": candidates,
        "evaluation": metrics,
        "boundary": "ML prioritizes controls; deterministic counterfactual replay verifies impact",
    }


def _workflow_reference(n: int = 900) -> np.ndarray:
    rng = np.random.default_rng(RANDOM_STATE + 2)
    rows = []
    for _ in range(n):
        step_count = int(np.clip(round(rng.normal(7.0, 1.0)), 5, 10))
        policy_checks = step_count + int(rng.integers(-1, 2))
        denied = int(rng.random() < 0.05)
        errors = int(rng.random() < 0.02)
        transitions = int(np.clip(round(rng.normal(2.2, 0.6)), 1, 4))
        repeated = int(rng.random() < 0.08)
        approval = int(rng.random() < 0.1)
        imbalance = float(abs(rng.normal(0.08, 0.05)))
        log_latency = float(np.clip(rng.normal(0.8, 0.45), 0.0, 2.5))
        rows.append([
            step_count,
            max(0, policy_checks),
            denied,
            errors,
            transitions,
            repeated,
            approval,
            imbalance,
            log_latency,
        ])
    return np.asarray(rows, dtype=float)


@lru_cache(maxsize=1)
def workflow_model() -> tuple[IsolationForest, np.ndarray, np.ndarray, np.ndarray]:
    reference = _workflow_reference()
    model = IsolationForest(
        n_estimators=180,
        contamination=0.06,
        random_state=RANDOM_STATE,
    )
    model.fit(reference)
    scores = model.decision_function(reference)
    means = reference.mean(axis=0)
    stds = reference.std(axis=0)
    return model, scores, means, stds


def workflow_features(events: list[dict]) -> np.ndarray:
    steps = [event for event in events if event.get("action") != "policy_check"]
    policy = [event for event in events if event.get("action") == "policy_check"]
    denied = sum(1 for event in policy if not event.get("allowed", False))
    errors = sum(1 for event in steps if event.get("status") == "error")

    agents = [event.get("agent") for event in steps if event.get("agent")]
    transitions = sum(1 for left, right in zip(agents, agents[1:]) if left != right)

    action_counts: dict[str, int] = {}
    for event in steps:
        action = str(event.get("action", "unknown"))
        action_counts[action] = action_counts.get(action, 0) + 1
    repeated = sum(max(0, count - 1) for count in action_counts.values())

    approval_signals = sum(1 for event in policy if "approval" in str(event.get("reason", "")).lower())
    counts = [agents.count(role) for role in ("red", "blue", "green")]
    total_steps = max(1, len(steps))
    imbalance = (max(counts) - min(counts)) / total_steps if counts else 0.0
    total_latency = sum(float(event.get("latency_ms", 0.0)) for event in steps)

    return np.asarray([
        len(steps),
        len(policy),
        denied,
        errors,
        transitions,
        repeated,
        approval_signals,
        imbalance,
        log1p(total_latency),
    ], dtype=float)


def score_workflow(events: list[dict]) -> dict:
    vector = workflow_features(events)
    model, reference_scores, means, stds = workflow_model()
    score = float(model.decision_function(vector.reshape(1, -1))[0])
    anomaly_percentile = round(float(np.mean(reference_scores >= score) * 100.0), 1)

    safe_stds = np.where(stds < 1e-6, 1.0, stds)
    z = (vector - means) / safe_stds
    deviations = [
        {
            "feature": name,
            "value": round(float(value), 4),
            "z_score": round(float(z_score), 3),
        }
        for name, value, z_score in zip(WORKFLOW_FEATURES, vector, z)
    ]
    deviations.sort(key=lambda item: abs(item["z_score"]), reverse=True)

    return {
        "model": "IsolationForest",
        "model_version": MODEL_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "anomaly_percentile": anomaly_percentile,
        "status": "REVIEW" if anomaly_percentile >= 95.0 else "NORMAL",
        "top_deviations": deviations[:3],
        "reference_rows": int(len(reference_scores)),
        "boundary": "workflow-health anomaly score; not a compromise probability",
    }


def ml_model_summary() -> dict:
    _, router_metrics = router_model()
    _, control_metrics = control_model()
    return {
        "version": MODEL_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "learned_model_router": {
            "model": "GradientBoostingClassifier",
            "features": ROUTER_FEATURES,
            "evaluation": router_metrics,
            "safety_boundary": "high-impact and approval-required tasks are deterministically forced to the highest-reliability route",
        },
        "green_control_ranker": {
            "model": "GradientBoostingRegressor",
            "features": CONTROL_FEATURES,
            "evaluation": control_metrics,
            "safety_boundary": "prediction prioritizes replay; deterministic counterfactual result remains authoritative",
        },
        "workflow_health": {
            "model": "IsolationForest",
            "features": WORKFLOW_FEATURES,
            "reference_rows": 900,
            "safety_boundary": "advisory orchestration-health signal only",
        },
        "data_boundary": "deterministic synthetic training/reference populations only",
    }
