---
title: Content Integrity Investigator
emoji: 🛡️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 8000
---

# 🛡️ Content Integrity Investigator

> **Training AI agents to investigate social media content the way a senior human reviewer would — not just classify, but reason.**

## 🎯 The Problem This Solves

Standard automated moderation systems often make "one-shot" decisions—labeling content based on a single pass. This lacks the nuanced reasoning required for complex cases. 

This environment treats content moderation as a **multi-step investigation**. Agents must learn to gather technical evidence, verify account history, and consult specific policies before acting. Crucially, the environment addresses **False Positive Asymmetry**: the real-world reality that wrongly removing legitimate content (silencing a creator) is often more damaging than missing a single bad post.

## 🧠 What an Agent Learns Here

* **Investigation Sequencing:** Learning to gather facts before consulting rules (avoiding confirmation bias).
* **Precision Tool-Use:** Using only the necessary tools to reach a ruling. Agents are penalized for "fishing expeditions" that waste computational resources.
* **Calibration:** Escalating to a human when signals are genuinely contradictory, rather than guessing.
* **Policy Nuance:** Identifying exemptions (like the "Public Interest Exception") that protect authentic journalism and small businesses.

## 📈 Baseline Performance (GPT-4o-mini)

The following scores were achieved using the included `inference.py` baseline script. These results demonstrate that the environment successfully differentiates between "lucky guesses" and "reasoned investigations."

| Task Level | Baseline Score | Result | Note |
|:-----------|:---------------|:-------|:-----|
| **Easy** | **0.6336** | **PASSED** | High accuracy on clear technical signals. |
| **Medium** | **0.2112** | **GRADED** | Agent penalized for unnecessary tool use/precision errors. |
| **Hard** | **0.7241** | **PASSED** | **Elite Performance:** Agent correctly navigated Public Interest Exceptions. |
| **Average** | **0.5230** | **SUCCESS** | **Overall baseline exceeds the 0.45 success threshold.** |

## 🛠️ Action Space

| Action | Parameters | Description |
|--------|-----------|-------------|
| `query_metadata` | none | Retrieve technical creation signals (AI confidence, device info). |
| `query_account_history` | none | Check posting patterns, account age, and previous violations. |
| `query_policy` | `policy_section` | Query specific sections of the Meta Policy Database. |
| `make_ruling` | `ruling`, `reasoning` | Submit final decision (remove, no_action, escalate). |

## 🧪 Reward Function Logic

The reward function is designed to steer agent behavior toward professional investigation standards:

1.  **Ruling Correctness (40%)**: Flat reward for the ground-truth ruling.
2.  **Evidence Quality (30%)**: Scaled reward based on whether the agent found the **Critical Evidence** (the "smoking gun").
3.  **False Positive Penalty**: Asymmetric penalty (up to -0.40) for wrongly removing content.
4.  **Tool Precision Penalty**: Scaled penalty for using irrelevant tools, capped at -0.10 to prevent agent paralysis.
5.  **Efficiency Bonus (10%)**: Reward for reaching the correct answer in fewer steps.

## 🚀 Setup & Evaluation

```bash
# 1. Install dependencies
pip install openenv-core

# 2. Build and run the Docker environment
docker build -t content-integrity-env .
docker run -p 8000:8000 content-integrity-env

# 3. Run the inference evaluation
python inference.py