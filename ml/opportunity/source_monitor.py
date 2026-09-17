"""
CuraTera AI - Step 10.6 Source Monitor

Responsibility:
    Fetch the latest government source for a scheme and determine
    whether the source content has changed since the previous check.

This component does NOT:
    - decide eligibility
    - classify policy changes
    - identify affected citizens
    - send notifications
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


# -------------------------------------------------
# Paths
# -------------------------------------------------

SNAPSHOT_PATH = Path(
    "data/processed/source_snapshots.json"
)

SOURCE_DIR = Path(
    "data/raw/original_sources"
)


# -------------------------------------------------
# HTTP settings
# -------------------------------------------------

TIMEOUT_SECONDS = 20

HEADERS = {
    "User-Agent": (
        "CuraTeraAI/1.0 "
        "(government-scheme-monitoring)"
    )
}


# -------------------------------------------------
# Initialize storage
# -------------------------------------------------

def initialize_storage() -> None:

    SNAPSHOT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    SOURCE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    if not SNAPSHOT_PATH.exists():

        SNAPSHOT_PATH.write_text(
            "{}",
            encoding="utf-8"
        )


# -------------------------------------------------
# Load snapshot metadata
# -------------------------------------------------

def load_snapshots() -> dict[str, Any]:

    initialize_storage()

    return json.loads(
        SNAPSHOT_PATH.read_text(
            encoding="utf-8"
        )
    )


# -------------------------------------------------
# Save snapshot metadata
# -------------------------------------------------

def save_snapshots(
    snapshots: dict[str, Any]
) -> None:

    initialize_storage()

    SNAPSHOT_PATH.write_text(
        json.dumps(
            snapshots,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )


# -------------------------------------------------
# Calculate content hash
# -------------------------------------------------

def calculate_hash(
    content: bytes
) -> str:

    return hashlib.sha256(
        content
    ).hexdigest()


# -------------------------------------------------
# Download source
# -------------------------------------------------

def fetch_source(
    url: str
) -> tuple[bytes, str]:

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=TIMEOUT_SECONDS
    )

    response.raise_for_status()

    content_type = (
        response.headers
        .get("Content-Type", "")
        .lower()
    )

    return response.content, content_type


# -------------------------------------------------
# Save source snapshot
# -------------------------------------------------

def save_source_snapshot(
    scheme_id: str,
    content: bytes,
    content_type: str,
) -> str:

    if "pdf" in content_type:

        extension = ".pdf"

    else:

        extension = ".html"

    path = (
        SOURCE_DIR
        / f"{scheme_id}{extension}"
    )

    path.write_bytes(
        content
    )

    return str(path)


# -------------------------------------------------
# Monitor one government source
# -------------------------------------------------

def monitor_source(
    scheme_id: str,
    source_url: str,
) -> dict[str, Any]:

    snapshots = load_snapshots()

    # ---------------------------------------------
    # Fetch latest source
    # ---------------------------------------------

    content, content_type = fetch_source(
        source_url
    )

    current_hash = calculate_hash(
        content
    )

    previous = snapshots.get(
        scheme_id
    )

    checked_at = datetime.now(
        timezone.utc
    ).isoformat()

    # ---------------------------------------------
    # First observation
    # ---------------------------------------------

    if previous is None:

        local_file = save_source_snapshot(
            scheme_id=scheme_id,
            content=content,
            content_type=content_type,
        )

        snapshots[scheme_id] = {
            "source_url": source_url,
            "last_checked": checked_at,
            "content_hash": current_hash,
            "local_file": local_file,
            "changed": False,
        }

        save_snapshots(
            snapshots
        )

        return {
            "scheme_id": scheme_id,
            "source_url": source_url,
            "changed": False,
            "first_observation": True,
            "old_hash": None,
            "new_hash": current_hash,
            "local_file": local_file,
        }

    # ---------------------------------------------
    # Compare previous hash
    # ---------------------------------------------

    old_hash = previous.get(
        "content_hash"
    )

    changed = (
        old_hash != current_hash
    )

    local_file = previous.get(
        "local_file"
    )

    # ---------------------------------------------
    # Save latest version only if changed
    # ---------------------------------------------

    if changed:

        local_file = save_source_snapshot(
            scheme_id=scheme_id,
            content=content,
            content_type=content_type,
        )

    # ---------------------------------------------
    # Update metadata
    # ---------------------------------------------

    snapshots[scheme_id] = {
        "source_url": source_url,
        "last_checked": checked_at,
        "content_hash": current_hash,
        "local_file": local_file,
        "changed": changed,
    }

    save_snapshots(
        snapshots
    )

    return {
        "scheme_id": scheme_id,
        "source_url": source_url,
        "changed": changed,
        "first_observation": False,
        "old_hash": old_hash,
        "new_hash": current_hash,
        "local_file": local_file,
    }