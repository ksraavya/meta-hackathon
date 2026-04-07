from .easy import EASY_EPISODES
from .medium import MEDIUM_EPISODES
from .hard import HARD_EPISODES
from .adversarial import ADVERSARIAL_EPISODES

# Mix adversarial episodes into the main pool
# adv episodes tagged easy/medium/hard slot into those pools
ADVERSARIAL_EASY = [e for e in ADVERSARIAL_EPISODES if e["task_level"] == "easy"]
ADVERSARIAL_MEDIUM = [e for e in ADVERSARIAL_EPISODES if e["task_level"] == "medium"]
ADVERSARIAL_HARD = [e for e in ADVERSARIAL_EPISODES if e["task_level"] == "hard"]

TASK_EASY = EASY_EPISODES + ADVERSARIAL_EASY
TASK_MEDIUM = MEDIUM_EPISODES + ADVERSARIAL_MEDIUM
TASK_HARD = HARD_EPISODES + ADVERSARIAL_HARD

ALL_EPISODES = TASK_EASY + TASK_MEDIUM + TASK_HARD

__all__ = [
    "EASY_EPISODES",
    "MEDIUM_EPISODES", 
    "HARD_EPISODES",
    "ADVERSARIAL_EPISODES",
    "TASK_EASY",
    "TASK_MEDIUM",
    "TASK_HARD",
    "ALL_EPISODES",
]