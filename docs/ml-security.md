# AegisMesh Security ML

AegisMesh uses three small learned models to improve orchestration efficiency and prioritization while keeping authorization and consequential security decisions outside the models.

## 1. Learned model router

`GradientBoostingClassifier`

Inputs include task class, scenario complexity, evidence count, graph depth, modeled risk, latency budget, cost budget, and whether approval is required.

The model recommends one of three abstract model classes:

- `compact-model`
- `reasoning-model`
- `high-reliability-model`

A deterministic safety override always forces `high_impact_proposal` and approval-required tasks to `high-reliability-model`, regardless of the learned prediction.

The checked-in evaluator trains and scores the router on a deterministic synthetic holdout. That result validates the routing pipeline only; it is not evidence about a proprietary or production LLM.

## 2. Green Agent control ranker

`GradientBoostingRegressor`

The ranker predicts which candidate control is most likely to reduce the synthetic attack-path score. Features include edge risk, path length, position in the path, downstream edges, original path risk, and control category.

The predicted reduction is advisory. Green applies the highest-ranked candidate to a copied synthetic environment and recomputes the path score with the deterministic counterfactual engine. The verified replay result is the value reported as the final reduction.

## 3. Workflow health anomaly detector

`IsolationForest`

The orchestration monitor uses step count, policy-check volume, denied tools, errors, agent transitions, repeated steps, approval signals, agent balance, and total step latency. It compares a run with a deterministic synthetic reference population and reports an anomaly percentile plus the largest feature deviations.

This score is an orchestration-health signal. It is not a probability that an agent, user, or system is compromised.

## Shared governance boundary

The models never:

- grant a tool permission;
- bypass the policy gateway;
- execute a consequential action;
- mutate the original scenario during replay;
- convert a model hypothesis into observed evidence;
- report synthetic holdout metrics as production efficacy.

All training and reference populations checked into this repository are synthetic and deterministic.