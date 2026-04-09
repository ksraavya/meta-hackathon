import asyncio
import os
import sys
import json
import textwrap
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
# Update this to your live Space URL
HF_SPACE_URL = os.getenv("ENV_URL", "https://sraavya-meta-hackathon.hf.space")

ENV_NAME = "content-integrity-investigator"
MAX_STEPS = 6
SUCCESS_SCORE_THRESHOLD = 0.45
MAX_TOTAL_REWARD = 1.0 

# --- Mandatory Logging Functions ---

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_val = str(success).lower()
    print(f"[END] success={success_val} steps={steps} score={score:.2f} rewards={rewards_str}", flush=True)

# --- Agent Logic ---

SYSTEM_PROMPT = """You are a content integrity investigator.
Analyze the post and evidence, then use tools to investigate or make a ruling.
Respond with ONLY a JSON object. Available actions:

1. {"action_type": "query_metadata"}
2. {"action_type": "query_account_history"}
3. {"action_type": "query_policy", "policy_section": "<section_name>"}
4. {"action_type": "make_ruling", "ruling": "<remove|no_action|escalate>", "reasoning": "<text>"}

CRITICAL: 'no_action', 'remove', and 'escalate' are NOT action_types. 
They are values for the "ruling" field WITHIN the "make_ruling" action.

CRITICAL: Do NOT invent policy sections. You MUST only use these exact names:
- synthetic_media_policy
- labeled_synthetic_media_exemption
- coordinated_inauthentic_behavior
- partially_synthetic_media
- public_interest_exception
- account_compromise_policy
- child_safety_policy
- violence_policy
- legal_proceedings_policy

Gather evidence before ruling. If unsure, escalate."""

def get_agent_action(client: OpenAI, observation: dict, history: List[str]) -> dict:
    user_prompt = f"Obs: {json.dumps(observation)}\nHistory: {history[-3:]}\nNext action?"
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=150,
        )
        text = completion.choices[0].message.content.strip()
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        return json.loads(text)
    except Exception:
        return {"action_type": "make_ruling", "ruling": "escalate", "reasoning": "Error fallback"}

# --- Task Runner ---

async def run_task(client: OpenAI, env, task_name: str, task_level: str) -> float:
    from models import InvestigatorAction
    
    # Initialize variables at start to prevent UnboundLocalError
    rewards = []
    steps_taken = 0
    success = False
    score = 0.01  # Initialize with the lower bound epsilon
    
    log_start(task=task_name, env=ENV_NAME, model=MODEL_NAME)
    
    try:
        result = await env.reset(task_level=task_level)
        obs_dict = result.observation.model_dump()
        
        for step in range(1, MAX_STEPS + 1):
            if result.done:
                break
            
            steps_taken = step
            action_dict = get_agent_action(client, obs_dict, [])
            
            try:
                # Validates against the literal policy names
                action_obj = InvestigatorAction(**action_dict)
                result = await env.step(action_obj)
                
                # Nudge individual rewards to stay positive (satisfies internal range checks)
                reward = max(0.01, result.reward or 0.0)
                error_msg = None
                done_status = result.done
            except Exception as e:
                # Catch hallucinations
                reward = 0.01 
                error_msg = "invalid_action_format"
                done_status = True 
                log_step(step, json.dumps(action_dict), reward, done_status, error_msg)
                break
            
            rewards.append(reward)
            obs_dict = result.observation.model_dump()
            log_step(step, json.dumps(action_dict), reward, done_status, error_msg)
            
            if done_status:
                break
        
        # Calculate base score
        raw_score = sum(rewards)
        
        # CLAMP & NUDGE: Ensure score is strictly 0 < score < 1
        # This satisfies: "Each task's score must be strictly between 0 and 1"
        score = min(max(raw_score, 0.01), 0.99)
        
        success = score >= SUCCESS_SCORE_THRESHOLD
        
    except Exception:
        score = 0.01 # Safe failure score
        
    finally:
        log_end(success, steps_taken, score, rewards)
    return score

async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    
    try:
        from client import ContentIntegrityEnv
        # Defined 3 tasks for the grader
        tasks = [("easy_case", "easy"), ("med_case", "medium"), ("hard_case", "hard")]
        
        async with ContentIntegrityEnv(base_url=HF_SPACE_URL) as env:
            for name, level in tasks:
                await run_task(client, env, name, level)
                
    except Exception:
        from server.content_integrity_environment import ContentIntegrityEnvironment
        
        class LocalWrapper:
            def __init__(self): self._e = ContentIntegrityEnvironment()
            async def reset(self, **kwargs):
                class R: pass
                r = R(); r.observation = self._e.reset(task_level=kwargs.get('task_level')); r.done = False
                return r
            async def step(self, action):
                class R: pass
                o, r, d, i = self._e.step(action)
                res = R(); res.observation = o; res.reward = r; res.done = d
                return res
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass

        async with LocalWrapper() as env:
            for name, level in [("easy_case", "easy"), ("med_case", "medium")]:
                await run_task(client, env, name, level)

if __name__ == "__main__":
    asyncio.run(main())