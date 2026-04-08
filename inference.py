"""
inference.py — Content Integrity Investigator
Judges run this file to evaluate our environment.

CRITICAL RULES:
- Log format must be exactly {"type": "START"/"STEP"/"END", ...}
- Must finish in under 20 minutes total
- Must use OpenAI client with env variables
- Must be named inference.py in root folder
- Scores must be between 0.0 and 1.0
"""

import asyncio
import json
import os
import sys
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ── Configuration from environment variables ─────────────────────────────────
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("HF_TOKEN", "")
if not API_KEY:
    raise ValueError("Missing API key (OPENAI_API_KEY or HF_TOKEN)")
MODEL_NAME   = os.environ.get("MODEL_NAME", "gpt-4o-mini")

# Your HuggingFace Space URL — update this on Day 5 after deploying
HF_SPACE_URL = os.environ.get(
    "ENV_URL",
    "http://localhost:8000"  # fallback to local for testing
)

ENV_NAME     = "content-integrity-investigator"
MAX_STEPS    = 6
MAX_TOTAL_REWARD = MAX_STEPS * 0.06 + 0.40 + 0.30 + 0.10  # approx max
SUCCESS_THRESHOLD = 0.45


# ── Logging — DO NOT CHANGE FIELD NAMES ──────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    """Called once at the start of each task."""
    print(json.dumps({
        "type":  "START",
        "task":  task,
        "env":   env,
        "model": model,
    }), flush=True)


def log_step(
    step: int,
    action: str,
    reward: float,
    done: bool,
    error: Optional[str] = None,
) -> None:
    """Called after every environment step."""
    print(json.dumps({
        "type":   "STEP",
        "step":   step,
        "action": action,
        "reward": round(reward, 4),
        "done":   done,
        "error":  error,
    }), flush=True)


def log_end(
    success: bool,
    steps: int,
    score: float,
    rewards: List[float],
) -> None:
    """Called once at the end of each task."""
    print(json.dumps({
        "type":    "END",
        "success": success,
        "steps":   steps,
        "score":   round(score, 4),
        "rewards": [round(r, 4) for r in rewards],
    }), flush=True)


# ── Agent — calls LLM to decide next action ──────────────────────────────────

SYSTEM_PROMPT = """You are a content integrity investigator for a social media platform.

Your job is to investigate posts and make a ruling: remove, no_action, or escalate.

AVAILABLE ACTIONS (respond with JSON only, no other text):

1. Query metadata:
   {"action_type": "query_metadata"}

2. Query account history:
   {"action_type": "query_account_history"}

3. Query a policy section:
   {"action_type": "query_policy", "policy_section": "<section>"}
   
   Available policy sections:
   - synthetic_media_policy
   - labeled_synthetic_media_exemption
   - coordinated_inauthentic_behavior
   - partially_synthetic_media
   - public_interest_exception
   - account_compromise_policy
   - child_safety_policy
   - violence_policy
   - legal_proceedings_policy

4. Make your ruling (only after investigating):
   {"action_type": "make_ruling", "ruling": "<remove|no_action|escalate>", "reasoning": "<your reason>"}

IMPORTANT RULES:
- Always gather evidence BEFORE making a ruling
- Consider false positives — wrongly removing real content is harmful
- If evidence is mixed or unclear, escalate rather than guess
- Respond with ONLY a JSON object. No explanation. No markdown.
- Avoid unnecessary tool use. If the case is clear, act quickly.
- If evidence is strong and clear, do not escalate unnecessarily.
"""


def get_agent_action(
    client: OpenAI,
    observation: dict,
    history: List[str],
    step: int,
) -> dict:
    """Ask the LLM what to do next. Returns a parsed action dict."""

    # Build context from observation
    obs_text = f"""
CASE:
Post: {observation.get('post_content', 'Unknown')}
Account: {observation.get('account_name', 'Unknown')} 
Account age: {observation.get('account_age_days', '?')} days
Platform: {observation.get('platform', 'Unknown')}
Step: {observation.get('step_number', step)}/{observation.get('max_steps', MAX_STEPS)}
Tools used: {observation.get('tools_used', [])}
Tools available: {observation.get('tools_available', [])}

LATEST RESULT:
{json.dumps(observation.get('latest_tool_result', 'No result yet'), indent=2)}

ALL EVIDENCE SO FAR:
{json.dumps(observation.get('accumulated_evidence', {}), indent=2)[:800]}

Message: {observation.get('message', '')}
"""

    recent_history = "\n".join(history[-3:]) if history else "No history."

    user_message = f"""{obs_text}

Recent actions:
{recent_history}

What is your next action? Respond with JSON only."""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            max_tokens=150,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()

        # Clean up if model wrapped response in markdown
        if "```" in raw:
            parts = raw.split("```")
            for part in parts:
                part = part.strip()
                if part.startswith("{") or part.startswith("json\n{"):
                    raw = part.replace("json\n", "").strip()
                    break

        return json.loads(raw)

    except json.JSONDecodeError:
        print(f"[DEBUG] JSON parse failed on: {raw[:100]}", flush=True)
        # Fallback: escalate if we can't parse
        return {
            "action_type": "make_ruling",
            "ruling": "escalate",
            "reasoning": "Parse error fallback",
        }
    except Exception as exc:
        print(f"[DEBUG] LLM call failed: {exc}", flush=True)
        return {
            "action_type": "make_ruling",
            "ruling": "escalate",
            "reasoning": "Error fallback",
        }


# ── Task Runner ───────────────────────────────────────────────────────────────

async def run_task(
    client: OpenAI,
    env,
    task_name: str,
    task_level: str,
) -> float:
    """
    Run one complete task (easy/medium/hard).
    Logs START, each STEP, and END.
    Returns normalized score 0.0-1.0.
    """
    from models import InvestigatorAction

    rewards: List[float] = []
    history: List[str]   = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=ENV_NAME, model=MODEL_NAME)

    try:
        # Reset environment to specific task level
        result = await env.reset(task_level=task_level)

        # Convert observation to dict for agent
        obs_dict = result.observation.model_dump()

        for step in range(1, MAX_STEPS + 1):

            if result.done:
                break

            # Get action from LLM agent
            action_dict = get_agent_action(client, obs_dict, history, step)
            action_str  = json.dumps(action_dict)

            # Validate action before sending
            try:
                action = InvestigatorAction(**action_dict)
            except Exception as e:
                print(f"[DEBUG] Invalid action at step {step}: {e}", flush=True)
                action = InvestigatorAction(
                    action_type="make_ruling",
                    ruling="escalate",
                    reasoning="Validation error fallback",
                )
                action_str = action.model_dump_json()

            # Step the environment
            try:
                result     = await env.step(action)
                reward     = result.reward or 0.0
                done       = result.done
                error      = None
                obs_dict   = result.observation.model_dump()

            except Exception as e:
                print(f"[DEBUG] env.step error: {e}", flush=True)
                reward = 0.0
                done   = True
                error  = str(e)

            rewards.append(reward)
            steps_taken = step

            log_step(step=step, action=action_str, reward=reward, done=done, error=error)

            history.append(
                f"Step {step}: {action_dict.get('action_type')} "
                f"→ reward {reward:+.4f}"
            )

            if done or error:
                break

        # Normalize score to 0.0-1.0
        total_reward = sum(rewards)
        score   = min(max(total_reward / MAX_TOTAL_REWARD, 0.0), 1.0)
        success = score >= SUCCESS_THRESHOLD

    except Exception as e:
        print(f"[DEBUG] Task-level error in {task_name}: {e}", flush=True)
        score   = 0.0
        success = False

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    # Import environment client
    try:
        from client import ContentIntegrityEnv
    except ImportError:
        print("[DEBUG] Could not import ContentIntegrityEnv", flush=True)
        sys.exit(1)

    # Three tasks — one per difficulty level
    # This satisfies the "3+ tasks with graders" requirement
    tasks = [
        ("content_integrity_easy",   "easy"),
        ("content_integrity_medium", "medium"),
        ("content_integrity_hard",   "hard"),
    ]

    all_scores: List[float] = []

    print(f"[DEBUG] Connecting to environment at: {HF_SPACE_URL}", flush=True)

    try:
        async with ContentIntegrityEnv(base_url=HF_SPACE_URL) as env:
            for task_name, task_level in tasks:
                print(f"[DEBUG] Starting task: {task_name}", flush=True)
                score = await run_task(client, env, task_name, task_level)
                all_scores.append(score)
                print(f"[DEBUG] Completed {task_name}: score={score:.4f}", flush=True)

    except Exception as e:
        print(f"[DEBUG] Connection error: {e}", flush=True)
        print("[DEBUG] Trying HTTP fallback...", flush=True)

        # HTTP fallback for local testing without WebSocket
        from server.content_integrity_environment import ContentIntegrityEnvironment
        from models import InvestigatorAction

        class LocalEnv:
            """Wraps the environment directly for local testing."""
            def __init__(self):
                self._env = ContentIntegrityEnvironment()
                self.done = False
                self.observation = None
                self.reward = 0.0

            async def reset(self, task_level=None):
                obs = self._env.reset(task_level=task_level)
                self.done = False

                class Result:
                    pass
                r = Result()
                r.observation = obs
                r.done = False
                r.reward = 0.0
                return r

            async def step(self, action):
                obs, reward, done, info = self._env.step(action)

                class Result:
                    pass
                r = Result()
                r.observation = obs
                r.reward = reward
                r.done = done
                return r

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        async with LocalEnv() as env:
            for task_name, task_level in tasks:
                print(f"[DEBUG] Starting task (local): {task_name}", flush=True)
                score = await run_task(client, env, task_name, task_level)
                all_scores.append(score)
                print(
                    f"[DEBUG] Completed {task_name}: score={score:.4f}",
                    flush=True,
                )

    avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
    print(
        f"[DEBUG] Final average score across all tasks: {avg:.4f}",
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())