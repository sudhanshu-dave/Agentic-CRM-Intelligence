import json
import logging
from typing import Any

from openai import OpenAI

from app.config import settings
from app.llm.prompts import build_llm_classification_messages
from app.llm.schemas import LLM_CLASSIFICATION_SCHEMA
from app.models import Email


logger = logging.getLogger(__name__)

LAST_LLM_ERROR: str | None = None


def get_last_llm_error() -> str | None:
    return LAST_LLM_ERROR


def set_last_llm_error(message: str | None) -> None:
    global LAST_LLM_ERROR
    LAST_LLM_ERROR = message


def classify_email_with_llm(
    email: Email,
    thread_context: str,
    rag_results: list[dict[str, Any]],
) -> dict[str, Any] | None:
    set_last_llm_error(None)

    if not settings.ENABLE_LLM_CLASSIFICATION:
        set_last_llm_error("ENABLE_LLM_CLASSIFICATION is false.")
        return None

    if not settings.GROQ_API_KEY:
        set_last_llm_error("GROQ_API_KEY is not loaded.")
        return None

    try:
        client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
        )

        messages = build_llm_classification_messages(
            email=email,
            thread_context=thread_context,
            rag_results=rag_results,
        )

        logger.warning("Calling Groq model: %s", settings.GROQ_MODEL)

        response = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,
            temperature=0.1,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "email_classification",
                    "strict": True,
                    "schema": LLM_CLASSIFICATION_SCHEMA,
                },
            },
        )

        content = response.choices[0].message.content

        if not content:
            set_last_llm_error("Groq returned empty content.")
            return None

        parsed = json.loads(content)

        parsed["model_used"] = settings.GROQ_MODEL
        parsed["llm_provider"] = "groq"
        parsed["rag_context"] = rag_results

        logger.warning("Groq classification succeeded using %s", settings.GROQ_MODEL)

        return parsed

    except Exception as exc:
        error_message = f"{type(exc).__name__}: {str(exc)}"
        set_last_llm_error(error_message)
        logger.exception("Groq classification failed. Falling back.")
        return None