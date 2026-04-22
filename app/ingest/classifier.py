from typing import Literal

from openai import OpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.ingest.taxonomy import (
    CLASSIFIER_SYSTEM_PROMPT,
    ClauseFamily,
    build_classifier_user_prompt,
)


class ClauseClassification(BaseModel):
    """Structured output for clause classification."""

    family: ClauseFamily | None
    confidence: Literal["high", "medium", "low"]
    rationale: str


@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def classify_clause(
    heading_text: str | None,
    section_path: str | None,
    clause_text: str,
) -> ClauseClassification:
    """Classify a clause into a family using OpenAI structured output."""
    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    response = client.chat.completions.parse(
        model=settings.openai_classifier_model,
        messages=[
            {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_classifier_user_prompt(
                    heading_text, section_path, clause_text
                ),
            },
        ],
        response_format=ClauseClassification,
    )
    return response.choices[0].message.parsed  # type: ignore[return-value]
