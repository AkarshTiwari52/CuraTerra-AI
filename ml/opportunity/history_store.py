from pathlib import Path
import pandas as pd


# -------------------------------------------------
# History file
# -------------------------------------------------

HISTORY_PATH = Path(
    "data/processed/opportunity_history.csv"
)


# -------------------------------------------------
# Columns stored in history
# -------------------------------------------------

HISTORY_COLUMNS = [
    "citizen_id",
    "scheme_id",
    "status",
    "first_detected_at",
    "last_checked_at",
    "last_notified_at",
    "notification_count",
]


# -------------------------------------------------
# Create history file if it does not exist
# -------------------------------------------------

def initialize_history():
    HISTORY_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not HISTORY_PATH.exists():

        df = pd.DataFrame(
            columns=HISTORY_COLUMNS
        )

        df.to_csv(
            HISTORY_PATH,
            index=False
        )


# -------------------------------------------------
# Load history
# -------------------------------------------------

def load_history():

    initialize_history()

    return pd.read_csv(
        HISTORY_PATH
    )


# -------------------------------------------------
# Check whether opportunity was already seen
# -------------------------------------------------

def opportunity_exists(
    citizen_id: str,
    scheme_id: str
) -> bool:

    df = load_history()

    if df.empty:
        return False

    match = df[
        (df["citizen_id"] == citizen_id)
        &
        (df["scheme_id"] == scheme_id)
    ]

    return not match.empty


# -------------------------------------------------
# Save new opportunity
# -------------------------------------------------

def add_opportunity(
    citizen_id: str,
    scheme_id: str,
    status: str,
    detected_at: str
):

    df = load_history()

    new_row = {
        "citizen_id": citizen_id,
        "scheme_id": scheme_id,
        "status": status,
        "first_detected_at": detected_at,
        "last_checked_at": detected_at,
        "last_notified_at": "",
        "notification_count": 0,
    }

    df = pd.concat(
        [
            df,
            pd.DataFrame([new_row])
        ],
        ignore_index=True
    )

    df.to_csv(
        HISTORY_PATH,
        index=False
    )


# -------------------------------------------------
# Update existing opportunity
# -------------------------------------------------

def update_opportunity(
    citizen_id: str,
    scheme_id: str,
    status: str,
    checked_at: str
):

    df = load_history()

    mask = (
        (df["citizen_id"] == citizen_id)
        &
        (df["scheme_id"] == scheme_id)
    )

    df.loc[
        mask,
        "status"
    ] = status

    df.loc[
        mask,
        "last_checked_at"
    ] = checked_at

    df.to_csv(
        HISTORY_PATH,
        index=False
    )