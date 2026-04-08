"""
Content Integrity Investigator — FINAL FINAL VERSION

This version is optimized for:
- Real-world moderation behavior
- Strong reward shaping
- Robustness against degenerate strategies
- Hackathon judging criteria alignment
"""

import uuid
import random
from typing import Tuple, Any, Dict, List, Optional

from pydantic import BaseModel
from models import InvestigatorAction, InvestigatorObservation
from episodes import TASK_EASY, TASK_MEDIUM, TASK_HARD, ALL_EPISODES
from server.policy_database import POLICY_DATABASE

class State(BaseModel):
    episode_id: str
    step_count: int


# ── Constants ─────────────────────────────────────────────

MAX_STEPS = 6
ALL_TOOLS = ["query_metadata", "query_account_history", "query_policy"]

WEIGHT_RULING     = 0.40
WEIGHT_EVIDENCE   = 0.30
WEIGHT_EFFICIENCY = 0.10

REWARD_RELEVANT_TOOL    = 0.06
REWARD_IRRELEVANT_TOOL  = 0.015

PENALTY_DUPLICATE_TOOL   = -0.05
PENALTY_NO_RULING        = -0.30
PENALTY_PREMATURE_POLICY = -0.05

ESCALATE_GOOD  = 0.05
ESCALATE_BAD   = -0.08

FP_PENALTY = {
    "very_high": -0.40,
    "high":      -0.25,
    "medium":    -0.15,
    "low":       -0.05,
    "none":       0.00,
}


# ── Environment ───────────────────────────────────────────

class ContentIntegrityEnvironment:

    _episode = None

    def __init__(self):
        super().__init__()
        self._episode_id = None
        self._tools_used = []
        self._policies_queried = []
        self._accumulated_evidence = {}
        self._step_count = 0

    # ── Reset ─────────────────────────────────────────────

    def reset(self, task_level: str = None):
        self._episode_id = str(uuid.uuid4())
        self._tools_used = []
        self._policies_queried = []
        self._accumulated_evidence = {}
        self._step_count = 0

        if task_level == "easy":
            pool = TASK_EASY
        elif task_level == "medium":
            pool = TASK_MEDIUM
        elif task_level == "hard":
            pool = TASK_HARD
        else:
            pool = ALL_EPISODES

        ContentIntegrityEnvironment._episode = random.choice(pool)

        return self._build_observation(None, 0.0, "New case assigned.")

    # ── Step ──────────────────────────────────────────────

    def step(self, action: InvestigatorAction):
        self._step_count += 1
        reward = 0.0
        done = False
        result = None
        msg = ""

        if action.action_type == "query_metadata":
            reward, result, msg = self._handle_metadata()

        elif action.action_type == "query_account_history":
            reward, result, msg = self._handle_account()

        elif action.action_type == "query_policy":
            reward, result, msg = self._handle_policy(action.policy_section)

        elif action.action_type == "make_ruling":
            done = True
            reward, msg = self._handle_ruling(action.ruling)

        if self._step_count >= MAX_STEPS and not done:
            done = True
            reward += PENALTY_NO_RULING
            msg = "Max steps reached without ruling."

        obs = self._build_observation(result, reward, msg)
        obs.episode_done = done

        return obs, reward, done, {}

    # ── Tool Handlers ─────────────────────────────────────

    def _handle_metadata(self):
        # 1. Safety check: If reset wasn't called or episode is lost
        if ContentIntegrityEnvironment._episode is None:
            self.reset("easy") # Auto-initialize to prevent crash
            
        if "query_metadata" in self._tools_used:
            return PENALTY_DUPLICATE_TOOL, None, "Metadata already queried."

        result = ContentIntegrityEnvironment._episode["available_tools"]["metadata"]
        self._tools_used.append("query_metadata")
        self._accumulated_evidence["metadata"] = result

        return self._tool_reward("query_metadata"), result, "Metadata retrieved."

    def _handle_account(self):
        if "query_account_history" in self._tools_used:
            return PENALTY_DUPLICATE_TOOL, None, "Account already queried."

        result = ContentIntegrityEnvironment._episode["available_tools"]["account_history"]
        self._tools_used.append("query_account_history")
        self._accumulated_evidence["account"] = result

        return self._tool_reward("query_account_history"), result, "Account retrieved."

    def _handle_policy(self, section):
        section = section or "synthetic_media_policy"

        if section in self._policies_queried:
            return PENALTY_DUPLICATE_TOOL, None, "Policy already queried."

        result = POLICY_DATABASE.get(section)
        self._policies_queried.append(section)

        if "query_policy" not in self._tools_used:
            self._tools_used.append("query_policy")

        self._accumulated_evidence["policy"] = result

        has_context = (
            "metadata" in self._accumulated_evidence or
            "account" in self._accumulated_evidence
        )

        reward = self._tool_reward("query_policy")

        if not has_context:
            reward += PENALTY_PREMATURE_POLICY
            msg = "Policy retrieved prematurely."
        else:
            msg = "Policy retrieved."

        return reward, result, msg

    # ── Tool Reward ───────────────────────────────────────

    def _tool_reward(self, tool):
        correct = set(ContentIntegrityEnvironment._episode.get("correct_tools", []))
        return REWARD_RELEVANT_TOOL if tool in correct else REWARD_IRRELEVANT_TOOL

    # ── Evidence Quality ──────────────────────────────────

    def _evidence_score(self):
        correct = set(ContentIntegrityEnvironment._episode.get("correct_tools", []))
        used = set(self._tools_used)

        if not used:
            return 0.0

        overlap = len(correct & used)
        score = overlap / max(len(correct), 1)

        # penalize unnecessary tools
        extra = len(used - correct)
        if extra > 0:
            score -= 0.2 * extra

        # penalize blind "use all tools"
        if len(used) == 3 and len(correct) < 3:
            score -= 0.1

        return max(0.0, min(1.0, score))

    # ── Final Reward ──────────────────────────────────────

    def _handle_ruling(self, ruling):
        reward = self._calculate_reward(ruling)
        correct = ContentIntegrityEnvironment._episode["correct_ruling"]
        return reward, f"Ruling={ruling}, Correct={correct}, Reward={reward}"

    def _calculate_reward(self, ruling):

        ep = ContentIntegrityEnvironment._episode
        correct = ep["correct_ruling"]
        correct_tools = set(ep.get("correct_tools", []))
        tools_used = set(self._tools_used)
        fp_risk = ep.get("false_positive_risk", "medium")
        adv = ep.get("adversarial_type")

        reward = 0.0

        # ── 1. Correctness ─────────────────────
        if ruling == correct:
            reward += WEIGHT_RULING
        elif ep.get("task_level") == "hard" and ruling == "escalate":
            if adv != "dont_be_cowardly":
                reward += 0.10

        # ── 2. Evidence Quality ─────────────────
        ev = self._evidence_score()
        reward += WEIGHT_EVIDENCE * ev

        # ── 3. Critical Evidence Bonus ──────────
        critical = set(ep.get("critical_evidence", []))
        if critical:
            if critical.issubset(tools_used):
                reward += 0.05
            else:
                reward -= 0.05

        # ── 4. Contradiction Awareness ─────────
        if ep.get("has_conflict") and ruling == correct:
            reward += 0.05

        # ── 5. Policy Ordering ─────────────────
        if "query_policy" in self._tools_used:
            idx = self._tools_used.index("query_policy")
            if idx == 0:
                reward -= 0.03

        # ── 6. Overconfidence Penalty ──────────
        if ruling != correct:
            if len(tools_used) == len(correct_tools):
                reward -= 0.12
            else:
                reward -= 0.05

        # ── 7. False Positive Protection ───────
        if correct == "no_action" and ruling == "remove":
            reward += FP_PENALTY.get(fp_risk, -0.15)

        # ── 8. Escalation Intelligence ─────────
        if ruling == "escalate":
            if ev < 0.5:
                reward += ESCALATE_GOOD
            else:
                reward += ESCALATE_BAD

        # ── 9. Tool Precision Penalty (FINAL FIX) ──
        extra_tools = tools_used - correct_tools
        if extra_tools:
            penalty = len(extra_tools) * (-0.05)
            reward += max(penalty, -0.10)  # capped correctly

        # ── 10. Adversarial Special ────────────
        if adv == "dont_be_cowardly":
            if ruling == "escalate":
                reward -= 0.40
            elif ruling == "no_action":
                reward -= 0.50

        # ── 11. Efficiency ─────────────────────
        if ruling == correct:
            s = self._step_count
            if s <= 2:
                reward += WEIGHT_EFFICIENCY
            elif s <= 3:
                reward += WEIGHT_EFFICIENCY * 0.7
            elif s <= 4:
                reward += WEIGHT_EFFICIENCY * 0.4

        return round(max(min(reward, 1.0), -0.5), 4)

    # ── Observation ───────────────────────────

    def _build_observation(self, result, reward, message):
        post = ContentIntegrityEnvironment._episode["post"]

        return InvestigatorObservation(
            post_content=post["content"],
            account_name=post["account_name"],
            account_age_days=post["account_age_days"],
            platform=post.get("platform", "Facebook"),
            step_number=self._step_count,
            max_steps=MAX_STEPS,
            task_level=ContentIntegrityEnvironment._episode.get("task_level"),
            tools_used=self._tools_used.copy(),
            tools_available=[t for t in ALL_TOOLS if t not in self._tools_used],
            latest_tool_result=result,
            accumulated_evidence=self._accumulated_evidence.copy(),
            message=message,
            step_reward=reward,
            episode_done=False,
        )

    @property
    def state(self):
        return State(
            episode_id=self._episode_id or "not_started",
            step_count=self._step_count,
        )
    
    def get_metadata(self):
        """Required by the OpenEnv server for the /metadata endpoint."""
        return {
            "name": "content-integrity-investigator",
            "description": "Environment for investigating content integrity.",
            "version": "1.0.0"
        }
    
    def close(self):
        """Cleanup environment (required by OpenEnv)."""
        pass

    async def reset_async(self, task_level: str = None):
        """Async wrapper for reset (required by OpenEnv)."""
        return self.reset(task_level)
    
    async def step_async(self, action):
        obs, reward, done, info = self.step(action)
        return obs