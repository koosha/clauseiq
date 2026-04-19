from app.ingest.metadata import extract_contract_metadata


def test_extracts_governing_law_explicit():
    text = "This Agreement is governed by the laws of the State of New York."
    md = extract_contract_metadata(text)
    assert md.governing_law == "New York"
    assert md.governing_law_confidence == "high"


def test_detects_saas_msa_title():
    text = "MASTER SERVICES AGREEMENT\n\nThis SaaS Master Services Agreement..."
    md = extract_contract_metadata(text)
    assert md.agreement_type == "SaaS_MSA"
    assert md.agreement_type_confidence in ("high", "medium")


def test_executed_status_from_signature_block():
    text = "IN WITNESS WHEREOF, the parties have executed this Agreement as of the date first written above."
    md = extract_contract_metadata(text)
    assert md.executed_status == "executed"


def test_missing_governing_law_returns_null_low_conf():
    md = extract_contract_metadata("just some generic contract language")
    assert md.governing_law is None
    assert md.governing_law_confidence == "low"
