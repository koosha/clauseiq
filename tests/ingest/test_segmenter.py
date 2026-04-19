from app.ingest.segmenter import segment_clauses, SegmenterBlock


def test_segmenter_groups_paragraphs_under_headings():
    blocks = [
        SegmenterBlock(text="Master Services Agreement", kind="heading", level=0),
        SegmenterBlock(text="1. Definitions", kind="heading", level=1),
        SegmenterBlock(text="\"Services\" means the cloud offering.", kind="paragraph"),
        SegmenterBlock(text="2. Payment Terms", kind="heading", level=1),
        SegmenterBlock(text="Customer shall pay invoices within 30 days.", kind="paragraph"),
        SegmenterBlock(text="Late payments accrue 1.5% monthly interest.", kind="paragraph"),
    ]

    clauses = segment_clauses(blocks)
    assert len(clauses) == 3
    assert clauses[0].heading_text == "1. Definitions"
    assert "cloud offering" in clauses[0].text_display
    assert clauses[1].heading_text == "2. Payment Terms"
    assert "30 days" in clauses[1].text_display
    assert "1.5% monthly" in clauses[2].text_display
    assert clauses[2].heading_text == "2. Payment Terms"


def test_segmenter_handles_no_headings():
    blocks = [SegmenterBlock(text="Some free text.", kind="paragraph")]
    clauses = segment_clauses(blocks)
    assert len(clauses) == 1
    assert clauses[0].heading_text is None


def test_segmenter_splits_payment_subclauses():
    blocks = [
        SegmenterBlock(text="4. Payment", kind="heading", level=1),
        SegmenterBlock(text="(a) Invoicing. Provider shall invoice monthly.", kind="paragraph"),
        SegmenterBlock(text="(b) Due Date. Payments are due within 30 days.", kind="paragraph"),
        SegmenterBlock(text="(c) Late Fees. Interest at 1.5% per month.", kind="paragraph"),
    ]
    clauses = segment_clauses(blocks)
    assert len(clauses) == 3
