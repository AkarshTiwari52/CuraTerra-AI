from typing import Optional


def build_notification(
    citizen_id: str,
    scheme_id: str,
    opportunity_type: str,
    language: str = "en",
    scheme_name: Optional[str] = None,
) -> dict:
    """
    Build a notification-ready payload.

    This function does NOT send the notification.
    It only prepares the payload for the app/backend team.
    """

    # -----------------------------------------
    # Scheme display name
    # -----------------------------------------

    display_name = scheme_name or scheme_id

    # -----------------------------------------
    # English message
    # -----------------------------------------

    if language == "en":

        if opportunity_type == "new_opportunity":
            title = "New government scheme opportunity"
            message = (
                f"You may be eligible for {display_name} "
                "based on your current profile."
            )

        elif opportunity_type == "missing_information":
            title = "More information needed"
            message = (
                f"Additional information is needed to complete "
                f"the eligibility check for {display_name}."
            )

        else:
            title = "CuraTera AI Update"
            message = (
                f"There is an update related to {display_name}."
            )

    # -----------------------------------------
    # Hindi message
    # -----------------------------------------

    elif language == "hi":

        if opportunity_type == "new_opportunity":
            title = "नई सरकारी योजना उपलब्ध है"
            message = (
                f"आपकी वर्तमान प्रोफ़ाइल के आधार पर "
                f"आप {display_name} के लिए पात्र हो सकते हैं।"
            )

        elif opportunity_type == "missing_information":
            title = "अधिक जानकारी आवश्यक है"
            message = (
                f"{display_name} की पात्रता जाँच पूरी करने के लिए "
                "कुछ अतिरिक्त जानकारी आवश्यक है।"
            )

        else:
            title = "CuraTera AI अपडेट"
            message = (
                f"{display_name} से संबंधित एक अपडेट उपलब्ध है।"
            )

    # -----------------------------------------
    # Hinglish message
    # -----------------------------------------

    elif language == "hinglish":

        if opportunity_type == "new_opportunity":
            title = "New government scheme opportunity"
            message = (
                f"Aapki current profile ke basis par "
                f"aap {display_name} ke liye eligible ho sakte hain."
            )

        elif opportunity_type == "missing_information":
            title = "More information needed"
            message = (
                f"{display_name} ki eligibility check complete karne ke liye "
                "kuch additional information chahiye."
            )

        else:
            title = "CuraTera AI Update"
            message = (
                f"{display_name} se related ek update available hai."
            )

    else:
        # -----------------------------------------
        # Safe fallback
        # -----------------------------------------

        title = "CuraTera AI Update"
        message = (
            f"There is an update related to {display_name}."
        )

    # -----------------------------------------
    # Notification payload
    # -----------------------------------------

    return {
        "citizen_id": citizen_id,
        "scheme_id": scheme_id,
        "notification_type": opportunity_type,
        "language": language,
        "title": title,
        "message": message,
        "priority": "normal",
        "status": "pending",
    }