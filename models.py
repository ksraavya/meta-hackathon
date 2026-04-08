from typing import Optional, Literal, Dict, List, Any
from pydantic import Field
from openenv.core.env_server.types import Action, Observation


class InvestigatorAction(Action):
    """
    The action an AI agent takes during a content integrity investigation.
    Agent must investigate before ruling — rushing to a ruling without
    evidence is penalized by the reward function.
    """

    action_type: Literal[
        "query_metadata",
        "query_account_history",
        "query_policy",
        "make_ruling",
    ] = Field(
        ...,
        description=(
            "Which action to take. Use query_* actions to gather evidence first. "
            "Use make_ruling only when you have enough evidence."
        ),
    )

    policy_section: Optional[
        Literal[
            "synthetic_media_policy",
            "labeled_synthetic_media_exemption",
            "coordinated_inauthentic_behavior",
            "partially_synthetic_media",
            "public_interest_exception",
            "account_compromise_policy",
            "child_safety_policy",
            "violence_policy",
            "legal_proceedings_policy",
        ]
    ] = Field(
        None,
        description=(
            "Which policy section to look up. "
            "Only used when action_type is query_policy."
        ),
    )

    ruling: Optional[Literal["remove", "no_action", "escalate"]] = Field(
        None,
        description=(
            "Your final ruling on the post. "
            "Only provide when action_type is make_ruling. "
            "remove = take down the post. "
            "no_action = post is fine, leave it up. "
            "escalate = not clear enough, send to human reviewer."
        ),
    )

    reasoning: Optional[str] = Field(
        None,
        description=(
            "Your reasoning for this action. "
            "Required when action_type is make_ruling. "
            "Used for LLM-based scoring of reasoning quality."
        ),
    )


class InvestigatorObservation(Observation):
    """
    What the agent sees at each step of the investigation.
    Evidence accumulates as the agent queries tools.
    The agent must use this to decide next steps.
    """

    # ── Case information (always visible) ──────────────────────────────
    post_content: str = Field(
        ...,
        description="The content of the post being reviewed.",
    )
    account_name: str = Field(
        ...,
        description="The name of the account that posted it.",
    )
    account_age_days: int = Field(
        ...,
        description="How old the account is in days.",
    )
    platform: str = Field(
        ...,
        description="Which platform the post is on.",
    )

    # ── Episode progress ────────────────────────────────────────────────
    step_number: int = Field(
        ...,
        description="Current step in this episode (starts at 0).",
    )
    max_steps: int = Field(
        ...,
        description="Maximum steps allowed before episode is force-ended.",
    )
    task_level: str = Field(
        ...,
        description="Difficulty level: easy / medium / hard.",
    )

    # ── Tool tracking ───────────────────────────────────────────────────
    tools_used: List[str] = Field(
        default_factory=list,
        description="List of tools the agent has already used this episode.",
    )
    tools_available: List[str] = Field(
        default_factory=list,
        description="Tools the agent can still use.",
    )

    # ── Evidence gathered ───────────────────────────────────────────────
    latest_tool_result: Optional[Any] = Field(
        None,
        description="Result from the most recent tool query.",
    )
    accumulated_evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="All evidence gathered so far this episode.",
    )

    # ── Step feedback ───────────────────────────────────────────────────
    message: str = Field(
        ...,
        description="Human-readable description of what just happened.",
    )
    step_reward: float = Field(
        default=0.0,
        description="Reward earned in this specific step.",
    )
    episode_done: bool = Field(
        default=False,
        description="Whether the episode has ended.",
    )