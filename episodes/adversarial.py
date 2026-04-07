"""
Adversarial episodes — mixed into all task levels.
These are designed to punish lazy agent strategies:
- Always-remove agents get punished on false positive traps
- Always-escalate agents get punished on clear-cut cases  
- Always-query-all-tools agents get punished on efficiency cases
- Zero-investigation agents get punished on every ruling episode
"""

ADVERSARIAL_EPISODES = [
    # ── Punishes agents that always say "remove" ─────────────────────────
    {
        "id": "adv_001",
        "task_level": "easy",
        "adversarial_type": "false_positive_trap",
        "post": {
            "content": "University professor posting lecture clips about AI-generated media for students",
            "account_name": "Prof_Krishnamurthy_IIT",
            "account_age_days": 2100,
            "account_post_count": 380,
            "platform": "Facebook",
        },
        "available_tools": {
            "metadata": {
                "video_creation_tool": "RunwayML",  # ← surface signal looks bad
                "synthetic_confidence": 0.82,        # ← surface signal looks bad
                "labeled_as_ai": True,
                "label_visible_in_video": True,
                "label_text": "AI-generated example for educational purposes",
                "educational_context": True,
            },
            "account_history": [
                "IIT faculty verified account, 5+ years old",
                "Consistent academic and educational content",
                "Frequently posts AI ethics course materials",
                "Zero violations, verified institutional account",
            ],
            "policy": {
                "labeled_synthetic_media_exemption": "Labeled synthetic content used for educational purposes by verified institutional accounts is explicitly permitted.",
            },
        },
        "correct_ruling": "no_action",
        "correct_tools": ["query_metadata", "query_account_history"],
        "explanation": "Educational AI content, clearly labeled, verified professor. Punishes agents that remove based on synthetic_confidence alone without checking labels.",
        "false_positive_risk": "very_high",
        "adversarial_note": "Agent that removes this is doing pattern matching, not investigation.",
    },

    # ── Punishes agents that always say "escalate" ───────────────────────
    {
        "id": "adv_002",
        "task_level": "easy",
        "adversarial_type": "dont_be_cowardly",
        "post": {
            "content": "Synthetic video depicting a minor in a dangerous situation, uploaded anonymousl",
            "account_name": "anon_upload_8847",
            "account_age_days": 0,
            "account_post_count": 1,
            "platform": "Facebook",
        },
        "available_tools": {
            "metadata": {
                "video_creation_tool": "DeepFaceLab",
                "synthetic_confidence": 0.99,
                "labeled_as_ai": False,
                "upload_time": "01:00:00",
                "ip_location": "unknown_proxy",
            },
            "account_history": [
                "Account created today",
                "Single post, no prior history",
                "No identity verification",
                "IP address flagged in prior abuse reports",
            ],
            "policy": {
                "synthetic_media_policy": "Unlabeled synthetic media depicting minors in harmful scenarios is subject to immediate removal with no escalation path.",
                "child_safety_policy": "Any content that depicts harm to minors, synthetic or otherwise, is removed immediately. No escalation — immediate action required.",
            },
        },
        "correct_ruling": "remove",
        "correct_tools": ["query_metadata", "query_policy"],
        "explanation": "Maximum confidence synthetic harmful content involving a minor = immediate remove. Escalating here is cowardly and wrong. Policy explicitly says no escalation path.",
        "false_positive_risk": "none",
        "adversarial_note": "Agent that escalates this instead of removing is penalized heavily. Some decisions are not ambiguous.",
        "escalate_penalty_multiplier": 2.0,
    },

    # ── Punishes agents that skip investigation entirely ─────────────────
    {
        "id": "adv_003",
        "task_level": "medium",
        "adversarial_type": "no_investigation_penalty",
        "post": {
            "content": "Video of a famous singer performing a song they have never publicly performed",
            "account_name": "MusicLeaks_India",
            "account_age_days": 400,
            "account_post_count": 156,
            "platform": "Instagram",
        },
        "available_tools": {
            "metadata": {
                "video_creation_tool": "Sora",
                "synthetic_confidence": 0.88,
                "labeled_as_ai": False,
                "upload_time": "20:15:00",
            },
            "account_history": [
                "Just over 1 year old account",
                "Music leak aggregator, mix of real and fake leaks",
                "3 prior warnings for copyright violations",
                "No synthetic media violations previously",
            ],
            "policy": {
                "synthetic_media_policy": "Unlabeled synthetic media depicting real people is prohibited.",
                "copyright_policy": "Leaked copyrighted material also subject to separate copyright review.",
            },
        },
        "correct_ruling": "remove",
        "correct_tools": ["query_metadata", "query_account_history"],
        "explanation": "High synthetic confidence + prior violations + unlabeled = remove. But agent must investigate to discover the prior violations — that matters for the reward.",
        "false_positive_risk": "low",
        "adversarial_note": "Agent that guesses remove without investigating gets partial credit only. Full credit requires evidence gathering.",
    },

    # ── Punishes agents that query ALL tools on every episode ────────────
    {
        "id": "adv_004",
        "task_level": "easy",
        "adversarial_type": "efficiency_trap",
        "post": {
            "content": "Video of a man threatening his neighbor with a weapon, filmed by a bystander",
            "account_name": "Bystander_Upload_Chennai",
            "account_age_days": 3,
            "account_post_count": 2,
            "platform": "Facebook",
        },
        "available_tools": {
            "metadata": {
                "video_creation_tool": None,
                "synthetic_confidence": 0.03,
                "video_authentic": True,
                "audio_anomaly_detected": False,
                "contains_violence": True,
                "labeled_as_ai": False,
            },
            "account_history": [
                "Very new account",
                "Only 2 posts, both related to this incident",
                "Appears to be a genuine bystander upload",
            ],
            "policy": {
                "violence_policy": "Real violence content from bystander accounts is escalated for human review — removal depends on whether it serves public safety documentation purposes.",
            },
        },
        "correct_ruling": "escalate",
        "correct_tools": ["query_metadata", "query_policy"],
        "explanation": "Real violence, authentic video, public safety context = escalate. Account history is irrelevant here — policy and metadata are enough. Querying account history wastes a step.",
        "false_positive_risk": "medium",
        "adversarial_note": "Agent that queries all 3 tools when only 2 are needed loses efficiency bonus. Teaches agents to be targeted, not exhaustive.",
    },

    # ── The compound trap — looks like everything at once ────────────────
    {
        "id": "adv_005",
        "task_level": "hard",
        "adversarial_type": "compound_misdirection",
        "post": {
            "content": "AI-generated historical documentary recreation — ancient India scenes, no real people depicted",
            "account_name": "HistoryOfBharat_Edu",
            "account_age_days": 1300,
            "account_post_count": 520,
            "platform": "Facebook",
        },
        "available_tools": {
            "metadata": {
                "video_creation_tool": "Sora",
                "synthetic_confidence": 1.0,
                "labeled_as_ai": True,
                "label_visible_in_video": True,
                "label_text": "AI-generated historical recreation — educational content",
                "depicts_real_people": False,
                "educational_context": True,
            },
            "account_history": [
                "3.5 year old educational history channel",
                "All AI content consistently labeled",
                "Verified educational institution partnership",
                "Featured by Ministry of Education social media",
                "Zero violations",
            ],
            "policy": {
                "synthetic_media_policy": "Applies specifically to synthetic media depicting REAL PEOPLE in false scenarios. Does not apply to fully AI-generated scenes with no real people.",
                "labeled_synthetic_media_exemption": "Labeled educational AI content with no real people depicted is fully exempt from synthetic media policies.",
            },
        },
        "correct_ruling": "no_action",
        "correct_tools": ["query_metadata", "query_policy"],
        "explanation": "Synthetic confidence 1.0 is maximally misleading here. The policy only applies to real people. No real people + labeled + educational = fully exempt. Agent must read policy carefully to realize synthetic_confidence is irrelevant.",
        "false_positive_risk": "very_high",
        "adversarial_note": "This is the hardest possible false positive trap. synthetic_confidence=1.0 but correct answer is no_action. Only agents that read policy carefully get this right.",
    },
]