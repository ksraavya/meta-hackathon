from typing import Any

try:
    from openenv.core.websocket_env_client import WebSocketEnvClient
    from openenv.core.types import StepResult

    class ContentIntegrityEnv(WebSocketEnvClient):

        def _step_payload(self, action) -> dict:
            return action.model_dump(exclude_none=True)

        def _parse_result(self, payload: dict) -> StepResult:
            try:
                from .models import InvestigatorObservation
            except ImportError:
                from models import InvestigatorObservation

            obs = InvestigatorObservation(**payload["observation"])
            return StepResult(
                observation=obs,
                reward=payload.get("reward", 0.0),
                done=payload.get("done", False),
                info=payload.get("info", {}),
            )

        def _parse_state(self, payload: dict) -> Any:
            return payload

except ImportError:
    # ✅ THIS is what runs locally
    from server.content_integrity_environment import ContentIntegrityEnvironment

    class ContentIntegrityEnv:
        def __init__(self, base_url=None):
            self.env = ContentIntegrityEnvironment()

        async def reset(self, task_level=None):
            obs = self.env.reset(task_level=task_level)
            return self._wrap(obs, 0.0, False)

        async def step(self, action):
            obs, reward, done, _ = self.env.step(action)
            return self._wrap(obs, reward, done)

        def _wrap(self, obs, reward, done):
            class Result:
                def __init__(self, o, r, d):
                    self.observation = o
                    self.reward = r
                    self.done = d
            return Result(obs, reward, done)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass