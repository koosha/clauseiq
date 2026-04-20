from unittest.mock import MagicMock, patch
from app.ingest.classifier import classify_clause, ClauseClassification
from app.ingest.taxonomy import ClauseFamily


@patch("app.ingest.classifier.OpenAI")
def test_classifier_parses_structured_output(MockOpenAI):
    client = MagicMock()
    MockOpenAI.return_value = client
    client.chat.completions.parse.return_value.choices = [
        MagicMock(
            message=MagicMock(
                parsed=ClauseClassification(
                    family=ClauseFamily.PAYMENT_TERMS,
                    confidence="high",
                    rationale="Clause about net 30 payment.",
                )
            )
        )
    ]

    result = classify_clause(
        heading_text="Payment Terms",
        section_path="Article 4",
        clause_text="Customer shall pay invoices within 30 days.",
    )
    assert result.family == ClauseFamily.PAYMENT_TERMS
    assert result.confidence == "high"


@patch("app.ingest.classifier.OpenAI")
def test_classifier_handles_null_family(MockOpenAI):
    client = MagicMock()
    MockOpenAI.return_value = client
    client.chat.completions.parse.return_value.choices = [
        MagicMock(
            message=MagicMock(
                parsed=ClauseClassification(
                    family=None,
                    confidence="low",
                    rationale="No clear family match.",
                )
            )
        )
    ]

    result = classify_clause(
        heading_text=None,
        section_path=None,
        clause_text="xyz",
    )
    assert result.family is None
    assert result.confidence == "low"
