"""
Synthetic policy database modeled on publicly documented
Meta content policies. In production this would connect
to Meta's actual internal policy API.
"""

POLICY_DATABASE = {
    "synthetic_media_policy": {
        "title": "Synthetic and AI-Generated Media Policy",
        "applies_to": "Unlabeled AI-generated media depicting real people",
        "rule": (
            "Unlabeled synthetic or AI-generated media that depicts real "
            "people in false or misleading scenarios is prohibited. This "
            "includes deepfakes, face-swaps, and voice clones. The key "
            "signal is: AI creation tool detected AND content is not "
            "labeled as AI-generated."
        ),
        "action": "remove",
        "exceptions": [
            "labeled_synthetic_media_exemption",
            "creator_consent when depicting themselves",
        ],
        "key_signals": [
            "video_creation_tool is not None",
            "labeled_as_ai is False",
            "synthetic_confidence > 0.5",
        ],
    },

    "labeled_synthetic_media_exemption": {
        "title": "Labeled Synthetic Media Exemption",
        "applies_to": "AI content that is clearly labeled",
        "rule": (
            "AI-generated content that is CLEARLY AND VISIBLY labeled as "
            "satirical, fictional, or AI-generated, and does not aim to "
            "deceive viewers, is explicitly permitted. The label must "
            "appear in the content itself, not just the caption. "
            "Established verified satire or educational accounts with "
            "clean records qualify. Creator consent to depict themselves "
            "using AI tools is an additional exemption qualifier."
        ),
        "action": "no_action",
        "exceptions": [],
        "key_signals": [
            "labeled_as_ai is True",
            "label_visible_in_video is True",
            "account has clean history",
        ],
    },

    "coordinated_inauthentic_behavior": {
        "title": "Coordinated Inauthentic Behavior Policy",
        "applies_to": "Bot networks and coordinated amplification",
        "rule": (
            "Networks of accounts acting in coordination to artificially "
            "amplify content violate platform integrity policies. Key "
            "signals include: abnormal posting velocity, identical "
            "captions shared across many accounts simultaneously, "
            "accounts created around the same time sharing the same "
            "content, automated posting patterns."
        ),
        "action": "remove",
        "exceptions": [],
        "key_signals": [
            "posting_pattern is automated_burst",
            "accounts_sharing_identical_caption > 500",
            "account very new with very high post count",
        ],
    },

    "partially_synthetic_media": {
        "title": "Partially Synthetic Media Policy",
        "applies_to": "Content where only part is AI-generated",
        "rule": (
            "Content where the video is authentic but audio, text "
            "overlays, or other elements may have been altered requires "
            "ESCALATION to human review rather than automated removal. "
            "Do not remove unilaterally. This applies when "
            "audio_anomaly_detected is True but video_authentic is also "
            "True. The partially synthetic nature means context matters "
            "and a human must decide."
        ),
        "action": "escalate",
        "exceptions": [],
        "key_signals": [
            "audio_anomaly_detected is True",
            "video_authentic is True",
        ],
    },

    "public_interest_exception": {
        "title": "Public Interest Exception",
        "applies_to": "Journalism and whistleblowing content",
        "rule": (
            "Content that may superficially appear to violate other "
            "policies but serves a clear and verifiable public interest "
            "— such as exposing genuine wrongdoing by public figures, "
            "documenting social issues, or supporting journalism — may "
            "be exempt from removal pending human review. Escalate "
            "rather than remove. Applies to verified journalist accounts "
            "and established NGOs with clean records."
        ),
        "action": "escalate",
        "exceptions": [],
        "key_signals": [
            "verified journalist or NGO account",
            "content documents real events",
            "account has established credibility",
        ],
    },

    "account_compromise_policy": {
        "title": "Account Compromise Policy",
        "applies_to": "Legitimate accounts showing signs of hijacking",
        "rule": (
            "Accounts showing signs of unauthorized access should be "
            "flagged for security review alongside any content action. "
            "Signs of compromise include: sudden login location change, "
            "abnormal posting frequency spike, content dramatically "
            "different from account history. A previously clean account "
            "history does NOT protect compromised account content — "
            "the content action and account action are separate."
        ),
        "action": "remove_and_flag",
        "exceptions": [],
        "key_signals": [
            "ip_location mismatched to account history",
            "sudden posting frequency spike",
            "content dramatically different from history",
        ],
    },

    "child_safety_policy": {
        "title": "Child Safety Policy",
        "applies_to": "Any content depicting harm to minors",
        "rule": (
            "Any content that depicts a minor in a dangerous, harmful, "
            "or exploitative scenario — whether synthetic or authentic — "
            "is subject to IMMEDIATE removal. There is NO escalation "
            "path for this policy. Do not escalate. Remove immediately. "
            "This is the only policy with no escalation option."
        ),
        "action": "remove_immediately",
        "exceptions": [],
        "key_signals": [
            "content involves a minor",
            "scenario is harmful or dangerous",
        ],
    },

    "violence_policy": {
        "title": "Real Violence Content Policy",
        "applies_to": "Authentic video of real violence",
        "rule": (
            "Authentic video content depicting real violence is "
            "escalated for human review rather than automatic removal. "
            "Context matters: bystander documentation of incidents may "
            "serve public safety or journalistic purposes. Human "
            "reviewers assess whether the content serves documentation "
            "purposes or glorifies violence."
        ),
        "action": "escalate",
        "exceptions": [],
        "key_signals": [
            "contains_violence is True",
            "video_authentic is True",
        ],
    },

    "legal_proceedings_policy": {
        "title": "Legal Proceedings Policy",
        "applies_to": "Content linked to active court cases",
        "rule": (
            "Content submitted as evidence in legal proceedings or "
            "directly documenting genuine legal events from verified "
            "journalism sources is protected. Standard content policies "
            "are SUSPENDED for content linked to active court cases "
            "pending review by the platform's legal team. Removing "
            "such content could constitute interference with legal "
            "proceedings. Always escalate — never remove unilaterally."
        ),
        "action": "escalate_to_legal",
        "exceptions": [],
        "key_signals": [
            "linked_to_active_court_case is True",
            "verified legal journalism account",
        ],
    },
}