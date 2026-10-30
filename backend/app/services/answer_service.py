
import json
import re
import urllib.error
import urllib.request
from collections import defaultdict

from app.services.search_service import search_documents


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5:3b"
MAX_HISTORY_MESSAGES = 8


def _normalize_text(value: str) -> str:
    """Normalize text for matching question wording."""
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _is_next_question_request(query: str) -> bool:
    """Check whether the user wants to advance to the next question."""
    return bool(
        re.search(
            r"\b(next|following)\s+question\b",
            query,
            re.IGNORECASE,
        )
    )


def _extract_question_bank(
    history: list[dict] | None,
) -> list[dict]:
    """
    Extract an ordered question list from a previous assistant response.

    Note: The displayed list index is not necessarily the original PDF
    question number. Original labels must be verified against PDF content.
    """
    if not history:
        return []

    for item in reversed(history):
        if (
            not isinstance(item, dict)
            or item.get("role") != "assistant"
        ):
            continue

        content = item.get("content", "")
        if not isinstance(content, str):
            continue

        lower = content.lower()

        if not any(
            marker in lower
            for marker in (
                "questions present",
                "here are the questions",
                "questions in unit",
            )
        ):
            continue

        questions = []

        for line in content.splitlines():
            list_match = re.match(
                r"^\s*\d+\.\s+(.*?)\s*$",
                line,
            )

            if not list_match:
                continue

            question_text = list_match.group(1).strip()

            if not question_text:
                continue

            questions.append(
                {
                    "text": question_text,
                    "normalized": _normalize_text(question_text),
                }
            )

        if len(questions) >= 2:
            return questions

    return []


def _find_last_answered_question(
    history: list[dict] | None,
    question_bank: list[dict],
) -> dict | None:
    """Match a previous assistant answer to a listed question."""
    if not history or not question_bank:
        return None

    for item in reversed(history):
        if (
            not isinstance(item, dict)
            or item.get("role") != "assistant"
        ):
            continue

        content = item.get("content", "")

        if not isinstance(content, str):
            continue

        normalized_content = _normalize_text(content)
        matches = []

        for question in question_bank:
            question_text = question["normalized"]

            if (
                len(question_text) >= 20
                and question_text in normalized_content
            ):
                matches.append(question)

        if matches:
            return max(
                matches,
                key=lambda question: len(question["normalized"]),
            )

    return None


def _resolve_next_question(
    query: str,
    history: list[dict] | None,
) -> tuple[str, str | None]:
    """
    Resolve a next-question request using the previously listed questions.

    If the last answered question cannot be matched, leave the query
    unchanged rather than guessing.
    """
    if not _is_next_question_request(query):
        return query, None

    question_bank = _extract_question_bank(history)

    last_question = _find_last_answered_question(
        history,
        question_bank,
    )

    if last_question is None:
        return query, None

    try:
        current_index = question_bank.index(last_question)
    except ValueError:
        return query, None

    next_index = current_index + 1

    if next_index >= len(question_bank):
        return query, None

    next_question = question_bank[next_index]

    resolved = (
        "Next question from the previously listed questions: "
        f"{next_question['text']}"
    )

    return resolved, resolved


def generate_answer(
    query: str,
    top_k: int = 3,
    document_id: str | None = None,
    document_ids: list[str] | None = None,
    conversation_history: list[dict] | None = None,
) -> dict:
    """Generate an answer using retrieved PDF content and chat history."""

    if not query or not query.strip():
        raise ValueError("Question cannot be empty.")

    history = conversation_history or []

    # Resolve conversational references before retrieval.
    retrieval_query, resolved_next_question = _resolve_next_question(
        query,
        history,
    )

    matches = search_documents(
        query=retrieval_query,
        top_k=top_k,
        document_id=document_id,
        document_ids=document_ids,
    )

    if not matches:
        return {
            "answer": (
                "I couldn't find relevant information in the selected "
                "documents. Try asking with more specific terms."
            ),
            "sources": [],
        }

    # Group retrieved chunks by document.
    grouped_chunks = defaultdict(list)
    sources = []
    seen_sources = set()

    for match in matches:
        metadata = match.get("metadata") or {}

        filename = metadata.get(
            "filename",
            "Unknown document",
        )

        document_key = (
            metadata.get("document_id")
            or filename
        )

        start_page = metadata.get("start_page", "?")
        end_page = metadata.get("end_page", start_page)

        grouped_chunks[document_key].append(
            {
                "filename": filename,
                "text": match.get("text", ""),
                "start_page": start_page,
                "end_page": end_page,
            }
        )

        source_key = (
            document_key,
            start_page,
            end_page,
        )

        if source_key not in seen_sources:
            sources.append(
                {
                    "filename": filename,
                    "start_page": start_page,
                    "end_page": end_page,
                    "distance": match.get("distance"),
                }
            )

            seen_sources.add(source_key)

    # Construct the retrieved context.
    context_parts = []

    for chunks in grouped_chunks.values():
        filename = chunks[0]["filename"]
        chunk_texts = []

        for chunk in chunks:
            text = chunk["text"].strip()

            if text:
                chunk_texts.append(text)

        if chunk_texts:
            context_parts.append(
                f"DOCUMENT: {filename}\n"
                + "\n\n".join(chunk_texts)
            )

    context = "\n\n--- NEXT DOCUMENT ---\n\n".join(
        context_parts
    )

    prompt = f"""
You are Knowledge Copilot, a conversational assistant that answers
questions using the user's uploaded PDF documents.

CURRENT USER MESSAGE:
{query}

RESOLVED NEXT QUESTION:
{resolved_next_question or "Not resolved from prior question list."}

RETRIEVED DOCUMENT CONTENT:
{context}

CONVERSATION RULES:
- Answer the user's latest request directly.
- Use conversation history to understand references and corrections.
- If the user corrects an answer, follow the corrected request.
- If the user requests only questions, provide only the questions.
- Preserve original question wording and numbering from the PDF.
- Respect the requested PDF, unit, chapter, topic, and question number.
- Do not mix questions from different units.
- If asked to explain a question, answer it rather than listing topics.
- If the user specifies 2, 5, or 10 marks, adjust the answer length
  and detail to that requirement.
- Use the retrieved PDF content as the primary evidence.
- Do not invent facts or claim that content appears in a PDF when it
  is not supported by the retrieved material.
- If the retrieved content is insufficient, explain the limitation.
- If a question number has multiple parts, such as 2(a) and 2(b),
  use the conversation context or ask which part the user means.
- Do not display source cards, page numbers, or a source list in
  the generated answer.

FOLLOW-UP QUESTION RULES:
1. If RESOLVED NEXT QUESTION contains a question, use it as the
   intended question for this response.
2. Do not repeat the previous question when the user asks for the next one.
3. Verify the intended question against the retrieved PDF content.
4. Do not treat the display-list index as the original PDF question number.
5. Preserve an original question label only when supported by the PDF.
6. If the next question cannot be identified reliably, ask the user
   to specify the question instead of inventing one.
7. Use the requested marks for the newly identified question.
8. Conversation history clarifies references but does not replace
   evidence from the selected PDF.

OUTPUT:
Provide a natural, clear answer that fulfills the latest request.
"""

    messages = [
        {
            "role": "system",
            "content": (
                "You are Knowledge Copilot, an enterprise knowledge "
                "assistant. Use retrieved PDF content as evidence. "
                "Use conversation history to understand follow-ups, "
                "but do not treat it as verified document evidence. "
                "Follow the user's latest request."
            ),
        }
    ]

    # Include recent conversation turns for conversational context.
    for item in history[-MAX_HISTORY_MESSAGES:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = item.get("content")

        if (
            role in {"user", "assistant"}
            and isinstance(content, str)
        ):
            content = content.strip()

            if content:
                messages.append(
                    {
                        "role": role,
                        "content": content[:4000],
                    }
                )

    messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0,
        },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=180,
        ) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. Ensure Ollama is running."
        ) from exc

    answer = (
        result.get("message", {})
        .get("content", "")
        .strip()
    )

    return {
        "answer": answer,
        "sources": sources,
    }
