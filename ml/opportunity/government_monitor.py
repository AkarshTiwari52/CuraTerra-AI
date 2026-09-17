from __future__ import annotations

from pathlib import Path
from datetime import datetime
import hashlib
import json
import shutil

from .policy_change_pipeline import extract_policy_from_pdf
from .change_detector import detect_changes
from .change_classifier import classify_change
from .affected_citizens import find_affected_citizens
from .eligibility_recheck import recheck_affected_citizens
from .step10_opportunity_bridge import bridge_recheck_results
from .step10_notification_bridge import build_notifications


class GovernmentMonitor:
    """
    Automatic government-side Step 10 controller.

    Flow:

    Government source
        ↓
    Source hash check
        ↓
    PDF extraction
        ↓
    Structured policy extraction
        ↓
    Previous policy lookup
        ↓
    Change detection
        ↓
    Change classification
        ↓
    Affected citizen detection
        ↓
    Eligibility re-check
        ↓
    Opportunity creation
        ↓
    Notification creation
    """

    HISTORY_FILE = Path(
        "data/processed/government_monitor_history.json"
    )

    SNAPSHOT_DIR = Path(
        "data/raw/original_sources"
    )

    def __init__(
        self,
        citizens: list[dict],
        rules_df,
        source_path: str | Path,
        scheme_id: str,
    ):
        self.citizens = citizens
        self.rules_df = rules_df

        self.source_path = Path(source_path)
        self.scheme_id = str(scheme_id)

    # ============================================================
    # STEP 1 — SOURCE MONITOR
    # ============================================================

    def monitor_source(self) -> dict:
        """
        Check whether the government document changed.

        The current source is treated as a local government-source
        snapshot. Later, the same method can be connected to a URL
        downloader from source_monitor.py.
        """

        if not self.source_path.exists():
            raise FileNotFoundError(
                f"Government source not found: {self.source_path}"
            )

        self.SNAPSHOT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.HISTORY_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        current_hash = self.calculate_file_hash(
            self.source_path
        )

        history = self.load_history()

        scheme_history = history.get(
            self.scheme_id,
            {}
        )

        previous_hash = scheme_history.get(
            "source_hash"
        )

        changed = (
            previous_hash is None
            or previous_hash != current_hash
        )

        # Save a snapshot of the current source
        snapshot_path = (
            self.SNAPSHOT_DIR
            / f"{self.scheme_id}_latest.pdf"
        )

        shutil.copy2(
            self.source_path,
            snapshot_path,
        )

        history[self.scheme_id] = {
            "source_hash": current_hash,
            "source_path": str(snapshot_path),
            "updated_at": datetime.now().isoformat(),
        }

        self.save_history(history)

        return {
            "changed": changed,
            "scheme_id": self.scheme_id,
            "source_path": str(snapshot_path),
            "source_hash": current_hash,
            "previous_hash": previous_hash,
        }

    # ============================================================
    # STEP 2 — FILE HASH
    # ============================================================

    @staticmethod
    def calculate_file_hash(
        file_path: Path,
    ) -> str:
        """
        Calculate SHA-256 hash of a file.
        """

        sha256 = hashlib.sha256()

        with file_path.open(
            "rb"
        ) as file:

            while True:
                chunk = file.read(8192)

                if not chunk:
                    break

                sha256.update(chunk)

        return sha256.hexdigest()

    # ============================================================
    # HISTORY
    # ============================================================

    def load_history(self) -> dict:
        """
        Load government monitor history.
        """

        if not self.HISTORY_FILE.exists():
            return {}

        try:
            content = self.HISTORY_FILE.read_text(
                encoding="utf-8"
            ).strip()

            if not content:
                return {}

            return json.loads(content)

        except (
            json.JSONDecodeError,
            OSError,
        ):
            return {}

    def save_history(
        self,
        history: dict,
    ) -> None:
        """
        Save monitor history.
        """

        self.HISTORY_FILE.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.HISTORY_FILE.write_text(
            json.dumps(
                history,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    # ============================================================
    # STEP 3 — DOCUMENT EXTRACTION
    # ============================================================

    def extract_document(
        self,
        source_path: str | Path,
    ) -> str:
        """
        Convert the PDF into structured policy information.

        extract_policy_from_pdf() is your existing
        policy pipeline function.
        """

        return extract_policy_from_pdf(
            Path(source_path) ,
            self.scheme_id
        )

    # ============================================================
    # STEP 4 — POLICY EXTRACTION
    # ============================================================

    def extract_policy(
        self,
        document_text,
    ) -> dict:
        """
        Convert extracted content into a policy dictionary.

        Your current extract_policy_from_pdf() may already return
        a structured policy dictionary. In that case, return it
        directly.

        If it returns text, this method keeps a safe fallback.
        """

        if isinstance(
            document_text,
            dict,
        ):
            return document_text

        raise TypeError(
            "extract_policy_from_pdf() did not return a "
            "structured policy dictionary."
        )

    # ============================================================
    # STEP 5 — PREVIOUS POLICY
    # ============================================================

    def get_previous_policy(
        self,
    ) -> dict | None:
        """
        Retrieve the previous structured policy.
        """

        history = self.load_history()

        scheme_history = history.get(
            self.scheme_id,
            {}
        )

        return scheme_history.get(
            "policy"
        )

    # ============================================================
    # SAVE CURRENT POLICY
    # ============================================================

    def save_policy(
        self,
        policy: dict,
    ) -> None:
        """
        Save the current policy as the latest policy.
        """

        history = self.load_history()

        if self.scheme_id not in history:
            history[self.scheme_id] = {}

        history[self.scheme_id][
            "policy"
        ] = policy

        history[self.scheme_id][
            "policy_saved_at"
        ] = datetime.now().isoformat()

        self.save_history(history)

    # ============================================================
    # STEP 6 — CHANGE DETECTION
    # ============================================================

    def detect_policy_changes(
        self,
        old_policy: dict,
        new_policy: dict,
    ) -> list[dict]:
        """
        Compare old and new policy.
        """

        return detect_changes(
            old_policy,
            new_policy,
        )

    # ============================================================
    # STEP 7 — CLASSIFY CHANGES
    # ============================================================

    def classify_policy_change(
        self,
        change: dict,
    ) -> dict:
        """
        Classify a single policy change.
        """

        return classify_change(
            change
        )

    # ============================================================
    # STEP 8 — FIND AFFECTED CITIZENS
    # ============================================================

    def find_affected(
        self,
        classified_changes: list[dict],
    ) -> list[dict]:
        """
        Identify citizens who may be affected by the change.
        """

        relevant_changes = []

        for change in classified_changes:

            if change.get(
                "action"
            ) == "recheck_eligibility":

                relevant_changes.append(
                    {
                        "field": change.get(
                            "field"
                        ),
                        "change_type": change.get(
                            "change_type"
                        ),
                        "old_value": change.get(
                            "old_value"
                        ),
                        "new_value": change.get(
                            "new_value"
                        ),
                    }
                )

        if not relevant_changes:
            return []

        change_input = {
            "scheme_id": self.scheme_id,
            "overall_action": "recheck_eligibility",
            "changes": relevant_changes,
        }

        return find_affected_citizens(
            citizens=self.citizens,
            change_info=change_input,
        )

    # ============================================================
    # STEP 9 — ELIGIBILITY RECHECK
    # ============================================================

    def recheck_eligibility(
        self,
        affected_citizens,
    ) -> list[dict]:
        """
        Re-check eligibility for affected citizens.
        """

        if not affected_citizens:
            return []

        return recheck_affected_citizens(
            affected_citizens=affected_citizens,
            rules_df=self.rules_df,
            scheme_id=self.scheme_id,
        )

    # ============================================================
    # STEP 10 — OPPORTUNITY
    # ============================================================

    def create_opportunities(
        self,
        eligibility_impacts: list[dict],
    ) -> list[dict]:
        """
        Convert newly eligible citizens into opportunities.
        """

        return bridge_recheck_results(
            eligibility_impacts
        )

    # ============================================================
    # STEP 11 — NOTIFICATIONS
    # ============================================================

    def create_notifications(
        self,
        opportunities: list[dict],
        language: str = "en",
    ) -> list[dict]:
        """
        Convert opportunities into notifications.
        """

        if not opportunities:
            return []

        return build_notifications(
            opportunities,
            language=language,
        )

    # ============================================================
    # MAIN AUTOMATIC PIPELINE
    # ============================================================

    def run(
        self,
        language: str = "en",
    ) -> dict:

        print("\n" + "=" * 70)
        print(
            "CURATERA GOVERNMENT POLICY MONITOR"
        )
        print("=" * 70)

        # --------------------------------------------------------
        # 1. SOURCE MONITOR
        # --------------------------------------------------------

        print(
            "\n[1] Checking government source..."
        )

        source_result = (
            self.monitor_source()
        )

        if not source_result["changed"]:

            print(
                "No source change detected."
            )

            return {
                "status": "no_change",
                "source_changed": False,
                "scheme_id": self.scheme_id,
                "changes": [],
                "classified_changes": [],
                "affected_citizens": [],
                "eligibility_impacts": [],
                "opportunities": [],
                "notifications": [],
            }

        print(
            "Government source changed."
        )

        # --------------------------------------------------------
        # 2. DOCUMENT EXTRACTION
        # --------------------------------------------------------

        print(
            "\n[2] Extracting document..."
        )

        document_text = (
            self.extract_document(
                source_result[
                    "source_path"
                ]
            )
        )

        if not document_text:
            return {
                "status": "failed",
                "reason":
                    "document_extraction_failed",
            }

        # --------------------------------------------------------
        # 3. STRUCTURED POLICY
        # --------------------------------------------------------

        print(
            "\n[3] Extracting structured policy..."
        )

        new_policy = (
            self.extract_policy(
                document_text
            )
        )

        if not new_policy:
            return {
                "status": "failed",
                "reason":
                    "policy_extraction_failed",
            }

        print(
            "Structured policy extracted."
        )

        # --------------------------------------------------------
        # 4. PREVIOUS POLICY
        # --------------------------------------------------------

        print(
            "\n[4] Loading previous policy..."
        )

        old_policy = (
            self.get_previous_policy()
        )

        # First time seeing this scheme
        if old_policy is None:

            print(
                "No previous policy found."
            )

            print(
                "Saving initial policy version."
            )

            self.save_policy(
                new_policy
            )

            return {
                "status":
                    "initial_version",
                "source_changed": True,
                "scheme_id":
                    self.scheme_id,
                "changes": [],
                "classified_changes": [],
                "affected_citizens": [],
                "eligibility_impacts": [],
                "opportunities": [],
                "notifications": [],
            }

        # --------------------------------------------------------
        # 5. CHANGE DETECTION
        # --------------------------------------------------------

        print(
            "\n[5] Detecting policy changes..."
        )

        changes = (
            self.detect_policy_changes(
                old_policy,
                new_policy,
            )
        )

        if not changes:

            print(
                "No policy field changes detected."
            )

            self.save_policy(
                new_policy
            )

            return {
                "status":
                    "no_meaningful_change",
                "source_changed": True,
                "scheme_id":
                    self.scheme_id,
                "changes": [],
                "classified_changes": [],
                "affected_citizens": [],
                "eligibility_impacts": [],
                "opportunities": [],
                "notifications": [],
            }

        print(
            f"Detected {len(changes)} change(s)."
        )

        for change in changes:

            print(
                f"  {change.get('field')}: "
                f"{change.get('old_value')} → "
                f"{change.get('new_value')}"
            )

        # --------------------------------------------------------
        # 6. CLASSIFICATION
        # --------------------------------------------------------

        print(
            "\n[6] Classifying changes..."
        )

        classified_changes = []

        for change in changes:

            classified = (
                self.classify_policy_change(
                    change
                )
            )

            classified_changes.append(
                classified
            )

        # --------------------------------------------------------
        # 7. AFFECTED CITIZENS
        # --------------------------------------------------------

        print(
            "\n[7] Finding affected citizens..."
        )

        affected_citizens = (
            self.find_affected(
                classified_changes
            )
        )

        print(
            "Affected citizens:",
            len(affected_citizens),
        )

        # --------------------------------------------------------
        # 8. ELIGIBILITY RECHECK
        # --------------------------------------------------------

        print(
            "\n[8] Re-checking eligibility..."
        )

        eligibility_impacts = (
            self.recheck_eligibility(
                affected_citizens
            )
        )

        for result in eligibility_impacts:

            print(
                f"  {result.get('citizen_id')}: "
                f"{result.get('old_status')} → "
                f"{result.get('new_status')} "
                f"({result.get('impact')})"
            )

        # --------------------------------------------------------
        # 9. SAVE POLICY
        # --------------------------------------------------------

        print(
            "\n[9] Saving new policy version..."
        )

        self.save_policy(
            new_policy
        )

        # --------------------------------------------------------
        # 10. OPPORTUNITIES
        # --------------------------------------------------------

        print(
            "\n[10] Creating opportunities..."
        )

        opportunities = (
            self.create_opportunities(
                eligibility_impacts
            )
        )

        print(
            "Opportunities created:",
            len(opportunities),
        )

        # --------------------------------------------------------
        # 11. NOTIFICATIONS
        # --------------------------------------------------------

        print(
            "\n[11] Creating notifications..."
        )

        notifications = (
            self.create_notifications(
                opportunities,
                language=language,
            )
        )

        print(
            "Notifications created:",
            len(notifications),
        )

        # --------------------------------------------------------
        # FINAL RESULT
        # --------------------------------------------------------

        result = {
            "status": "completed",
            "timestamp":
                datetime.now().isoformat(),

            "source_changed": True,

            "scheme_id":
                self.scheme_id,

            "changes":
                changes,

            "classified_changes":
                classified_changes,

            "affected_citizens":
                affected_citizens,

            "eligibility_impacts":
                eligibility_impacts,

            "opportunities":
                opportunities,

            "notifications":
                notifications,
        }

        print(
            "\n" + "=" * 70
        )
        print(
            "GOVERNMENT MONITOR COMPLETE"
        )
        print(
            "=" * 70
        )

        return result