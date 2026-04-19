import re
from dataclasses import dataclass
from typing import Literal

Confidence = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class ContractMetadata:
    agreement_type: str | None
    agreement_type_confidence: Confidence
    executed_status: str | None
    executed_status_confidence: Confidence
    governing_law: str | None
    governing_law_confidence: Confidence


US_STATES = [
    "New York", "California", "Delaware", "Texas", "Massachusetts", "Illinois",
    "Washington", "Florida", "Pennsylvania", "Virginia", "Georgia", "Colorado",
]


GOVERNING_LAW_PATTERNS = [
    re.compile(
        r"governed\s+by\s+(?:and\s+construed\s+in\s+accordance\s+with\s+)?"
        r"the\s+laws?\s+of\s+(?:the\s+State\s+of\s+)?([A-Z][A-Za-z\s]+?)(?=[,.]|$)",
        re.IGNORECASE,
    ),
    re.compile(r"State\s+of\s+([A-Z][A-Za-z\s]+?)\s+law", re.IGNORECASE),
]


def extract_contract_metadata(text: str) -> ContractMetadata:
    agreement_type, at_conf = _detect_agreement_type(text)
    executed, ex_conf = _detect_executed(text)
    gov_law, gl_conf = _detect_governing_law(text)

    return ContractMetadata(
        agreement_type=agreement_type,
        agreement_type_confidence=at_conf,
        executed_status=executed,
        executed_status_confidence=ex_conf,
        governing_law=gov_law,
        governing_law_confidence=gl_conf,
    )


def _detect_agreement_type(text: str) -> tuple[str | None, Confidence]:
    head = text[:2000]
    if re.search(r"master\s+services?\s+agreement", head, re.IGNORECASE):
        if re.search(r"saas|software[- ]as[- ]a[- ]service|subscription", head, re.IGNORECASE):
            return "SaaS_MSA", "high"
        return "SaaS_MSA", "medium"
    return None, "low"


def _detect_executed(text: str) -> tuple[str | None, Confidence]:
    if re.search(r"in\s+witness\s+whereof", text, re.IGNORECASE):
        return "executed", "high"
    if re.search(r"executed\s+(?:this|as\s+of)", text, re.IGNORECASE):
        return "executed", "high"
    return None, "low"


def _detect_governing_law(text: str) -> tuple[str | None, Confidence]:
    for pat in GOVERNING_LAW_PATTERNS:
        m = pat.search(text)
        if m:
            candidate = m.group(1).strip().rstrip(",.")
            for st in US_STATES:
                if candidate.lower() == st.lower():
                    return st, "high"
            if candidate and len(candidate) < 40:
                return candidate, "medium"
    return None, "low"
