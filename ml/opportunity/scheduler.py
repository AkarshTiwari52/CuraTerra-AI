"""
CuraTera AI - Unified Opportunity Scheduler
"""

from __future__ import annotations

import sys
from pathlib import Path
import time
from datetime import datetime, timezone
from typing import Any

# -------------------------------------------------
# Add project root to Python path
# -------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import pandas as pd

from ml.opportunity.proactive_engine import run_daily_check
from ml.opportunity.opportunity_builder import build_opportunities
from ml.opportunity.notification_decision import decide_notifications
from ml.opportunity.notification_builder import build_notification
from ml.opportunity.government_monitor import GovernmentMonitor

from ml.opportunity.government_monitor import GovernmentMonitor


# ============================================================
# CONFIGURATION
# ============================================================

from pathlib import Path

RULES_PATH = Path(
    "data/processed/eligibility_rules_preview.csv"
)

GOVERNMENT_SOURCE_PATH = Path(
    "data/raw/original_sources/Post-matric-guidelines-15032023.pdf"
)

GOVERNMENT_SCHEME_ID = "S039"
CHECK_INTERVAL_SECONDS = 60


# ============================================================
# LOAD ELIGIBILITY RULES
# ============================================================

def load_rules() -> pd.DataFrame:
    return pd.read_csv(RULES_PATH)


# ============================================================
# STEP 9
# ============================================================

def run_step9_cycle(
    citizens: list[dict[str, Any]]
) -> list[dict[str, Any]]:

    rules_df = load_rules()

    print("\n" + "-" * 70)
    print("STEP 9 - PROACTIVE CITIZEN OPPORTUNITY CHECK")
    print("-" * 70)

    results = run_daily_check(
        citizens=citizens,
        rules_df=rules_df,
    )

    notifications = []

    for result in results:

        citizen_id = result["citizen_id"]

        opportunity_result = build_opportunities(
            citizen_id=citizen_id,
            eligibility_results=result["all_results"],
            checked_at=result["checked_at"],
        )

        actions = decide_notifications(
            opportunity_result
        )

        for action in actions:

            if action["action"] == "notify":

                notification = build_notification(
                    citizen_id=citizen_id,
                    scheme_id=action["scheme_id"],
                    opportunity_type="new_opportunity",
                    language="en",
                )

                notifications.append(
                    notification
                )

    return notifications


# ============================================================
# STEP 10
# ============================================================

def run_step10_cycle(
    citizens: list[dict[str, Any]]
):
    """
    Run the complete government policy-change pipeline.

    GovernmentMonitor internally performs:

        source monitoring
            ↓
        policy extraction
            ↓
        change detection
            ↓
        change classification
            ↓
        affected citizens
            ↓
        eligibility re-check
            ↓
        opportunity
            ↓
        notification
    """

    print("\n" + "-" * 70)
    print("STEP 10 - GOVERNMENT POLICY MONITOR")
    print("-" * 70)

    rules_df = load_rules()

    monitor = GovernmentMonitor(
        citizens=citizens,
        rules_df=rules_df,
        source_path=GOVERNMENT_SOURCE_PATH,
        scheme_id=GOVERNMENT_SCHEME_ID,
    )

    result = monitor.run(
        language="en"
    )

    return result


# ============================================================
# RUN ONE UNIFIED CYCLE
# ============================================================

def run_full_cycle(
    citizens: list[dict[str, Any]]
):
    """
    Run Step 9 and Step 10 in the same scheduler cycle.
    """

    print("\n" + "=" * 70)
    print("CURATERA AI - UNIFIED SCHEDULER CYCLE")
    print("=" * 70)

    # --------------------------------------------------------
    # STEP 9
    # --------------------------------------------------------

    step9_notifications = run_step9_cycle(
        citizens
    )

    print(
        f"\nStep 9 notifications: "
        f"{len(step9_notifications)}"
    )

    for notification in step9_notifications:

        print("\nStep 9 Notification:")
        print(notification)

    # --------------------------------------------------------
    # STEP 10
    # --------------------------------------------------------

    step10_result = run_step10_cycle(
        citizens
    )

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("UNIFIED CYCLE COMPLETE")
    print("=" * 70)

    print(
        "Step 9 notifications:",
        len(step9_notifications),
    )

    print(
        "Step 10 status:",
        step10_result.get("status"),
    )

    print(
        "Step 10 opportunities:",
        len(
            step10_result.get(
                "opportunities",
                []
            )
        ),
    )

    print(
        "Step 10 notifications:",
        len(
            step10_result.get(
                "notifications",
                []
            )
        ),
    )

    return {
        "step9_notifications":
            step9_notifications,

        "step10_result":
            step10_result,
    }


# ============================================================
# CONTINUOUS SCHEDULER
# ============================================================

def start_scheduler(
    citizens: list[dict[str, Any]]
):

    print("=" * 70)
    print("CURATERA AI - UNIFIED SCHEDULER")
    print("=" * 70)

    print(
        f"Check interval: "
        f"{CHECK_INTERVAL_SECONDS} seconds"
    )

    while True:

        now = datetime.now(
            timezone.utc
        ).isoformat()

        print(
            f"\nRunning scheduled cycle: "
            f"{now}"
        )

        try:

            run_full_cycle(
                citizens
            )

        except Exception as exc:

            print(
                "\nScheduler error:"
            )

            print(exc)

        print(
            f"\nNext cycle in "
            f"{CHECK_INTERVAL_SECONDS} seconds..."
        )

        time.sleep(
            CHECK_INTERVAL_SECONDS
        )


# ============================================================
# DEVELOPMENT TEST
# ============================================================

if __name__ == "__main__":

    citizens = [

        {
            "citizen_id": "C001",
            "profile": {
                "age": 14,
                "gender": "female",
                "state": "Maharashtra",
                "district": "Pune",
                "social_category": "VJNT",
                "annual_family_income": 60000,
                "occupation": "Student",
                "school_class": 9,
                "student_status": True,
            },
        },

        {
            "citizen_id": "C002",
            "profile": {
                "age": 22,
                "gender": "male",
                "state": "Maharashtra",
                "district": "Pune",
                "social_category": "General",
                "annual_family_income": 60000,
                "occupation": "Student",
                "education_level": "Graduated",
                "student_status": True,
            },
        },

    ]

    # --------------------------------------------------------
    # RUN ONE COMPLETE CYCLE
    # --------------------------------------------------------

    result = run_full_cycle(
        citizens
    )

    print("\n" + "=" * 70)
    print("FINAL SCHEDULER RESULT")
    print("=" * 70)

    print(result)

    # --------------------------------------------------------
    # For continuous scheduler testing:
    #
    # start_scheduler(citizens)
    # --------------------------------------------------------