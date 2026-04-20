from enum import StrEnum


class ClauseFamily(StrEnum):
    """20-family taxonomy for SaaS MSA clauses."""

    DEFINITIONS = "definitions"
    FEES_AND_PRICING = "fees_and_pricing"
    PAYMENT_TERMS = "payment_terms"
    LATE_PAYMENT_AND_SUSPENSION = "late_payment_and_suspension"
    TERM_AND_RENEWAL = "term_and_renewal"
    TERMINATION = "termination"
    SERVICE_LEVELS = "service_levels"
    SUPPORT_AND_MAINTENANCE = "support_and_maintenance"
    DATA_SECURITY = "data_security"
    DATA_PRIVACY = "data_privacy"
    CONFIDENTIALITY = "confidentiality"
    INTELLECTUAL_PROPERTY = "intellectual_property"
    WARRANTIES_AND_DISCLAIMERS = "warranties_and_disclaimers"
    LIMITATION_OF_LIABILITY = "limitation_of_liability"
    INDEMNIFICATION = "indemnification"
    INSURANCE = "insurance"
    GOVERNING_LAW_AND_JURISDICTION = "governing_law_and_jurisdiction"
    DISPUTE_RESOLUTION = "dispute_resolution"
    ASSIGNMENT_AND_CHANGE_OF_CONTROL = "assignment_and_change_of_control"
    GENERAL_BOILERPLATE = "general_boilerplate"


CLASSIFIER_SYSTEM_PROMPT = (
    "You classify clauses from executed SaaS Master Services Agreements into "
    "one of 20 families. If no family clearly fits, return family=null with "
    "confidence=low. Never invent new family names."
)


def build_classifier_user_prompt(
    heading_text: str | None,
    section_path: str | None,
    clause_text: str,
) -> str:
    """Build the user prompt for the classifier."""
    return (
        f'HEADING: "{heading_text or ""}"\n'
        f'SECTION PATH: "{section_path or ""}"\n'
        f"CLAUSE TEXT:\n{clause_text}"
    )
