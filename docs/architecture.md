# AegisMesh Architecture

AegisMesh is a defensive, simulation-only reference architecture for coordinated security agents.

## Trust model

The design assumes agent output can be wrong, incomplete, or manipulated. Security authority therefore sits outside the agents.

- Agent proposals are typed inputs to deterministic policy checks.
- Tools are allow-listed by agent role.
- Consequential actions are marked as approval-required and are not executed by the public lab.
- Evidence references are retained separately from hypotheses.
- Counterfactual replay operates on a copy of synthetic state.

## Workflow

1. Load a versioned synthetic enterprise scenario.
2. Red Agent selects the modeled path and emits synthetic evidence.
3. Blue Agent correlates evidence, retrieves local security context, and reconstructs the path.
4. Green Agent evaluates candidate controls against the same path.
5. Counterfactual replay applies one control to copied state and re-scores the synthetic path.
6. Observability records policy decisions, agent steps, and timing.

## Production evolution

A real deployment would require authenticated connectors, tenant isolation, durable workflow state, signed tool manifests, vector/hybrid retrieval, model/version provenance, cost and latency budgets, replay-safe idempotent writes, approval workflows, temporal validation, drift monitoring, and independent security evaluation.

The public repository intentionally does not include live penetration-testing tools, arbitrary shell execution, autonomous remediation, credential access, or external targeting.
