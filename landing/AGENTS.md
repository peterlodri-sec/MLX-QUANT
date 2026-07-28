# AGENTS.md — Axiom Quant Agentic Architecture & Protocol Standard

## Overview
This document specifies the interaction contract, tool integration protocols, and execution loop requirements for autonomous AI agents operating within the **AXIOM QUANT** codebase and platform ecosystem.

---

## 1. Agent Roles & Capabilities

| Agent Role | Subagent Type | Primary Objectives & Tools |
| :--- | :--- | :--- |
| **Graph Topology Agent** | `research` / `self` | Cycle rank $\beta_1$, holonomy field extensions, Erdős $G(n,p)$ sampling |
| **Stochastic Calculus Agent** | `research` / `self` | Black-Scholes Greeks ($\Delta, \Gamma, \Theta, \nu$), Geometric Brownian Motion |
| **Markowitz QP Agent** | `research` / `self` | Convex quadratic programming, efficient frontier, tangency portfolios |
| **Loop Engineering Agent** | `self` | Backyard Ultra iteration loops, state persistence (`working_memory.md`), TDD cycles |

---

## 2. Model Context Protocol (MCP) Server Infrastructure

Agents operating on this codebase MUST utilize the following Model Context Protocol (MCP) servers:

1. **`codebase-memory-mcp`**:
   - `search_graph(name_pattern)`: Discover functions, modules, and routes.
   - `trace_path(function_name, direction)`: Trace call graphs and dependencies.
   - `get_code_snippet(qualified_name)`: Retrieve authoritative source implementations.
2. **`cloudrun`**:
   - `list_projects()`, `get_service()`, `deploy_local_folder()`: Manage GCP Cloud Run deployments.
3. **`chrome-devtools-mcp`**:
   - `lighthouse_audit()`, `performance_analyze_insight()`: Audit web performance and CWV.

---

## 3. The Backyard Ultra Loop Contract

Every long-horizon agent execution turn MUST conform to the **Backyard Ultra Loop Engineering Contract**:

```python
# The Deterministic Agent Loop Contract
def backyard_ultra_loop(agent, task_goal):
    lap = 0
    state = load_persisted_state()

    while not task_goal.is_fulfilled(state):
        lap += 1
        skills = select_skills(state.current_needs)
        observation = agent.step(task_goal, state, skills)
        success, verification_log = verify_runtime(observation)
        state.update(observation, verification_log)
        persist_state_to_disk(state)

    return state.final_artifact
```

---

## 4. API Endpoints for Agents

- **GCP ADK Multi-Agent Orchestrator**: `GET https://axiomquant.org/api/v1/adk/agent?query={prompt}`
- **Markowitz QP Solver**: `GET https://axiomquant.org/api/v1/markowitz?universe=BigTech`
- **Black-Scholes Greeks Engine**: `GET https://axiomquant.org/api/v1/black-scholes?S=100&K=105&T=0.5&r=0.05&vol=0.20`
