import re
from app.config import get_settings
from app.utils.logger import logger

_hf_pipeline = None

DISCLAIMER = "This information is for educational purposes only and does not constitute legal advice. Please consult a qualified lawyer for advice specific to your situation."
DISCLAIMER_HI = "यह जानकारी केवल शैक्षिक उद्देश्यों के लिए है और यह कानूनी सलाह नहीं है। अपनी स्थिति के लिए किसी योग्य वकील से परामर्श करें।"

SYSTEM_PROMPT = """You are a legal assistant specialized in Indian law. Answer the user's question using ONLY the provided context. Be specific and cite sections.

Context:
{context}

Question: {query}

Answer in this exact format:
Short Answer: (1-2 sentences)
Explanation: (detailed answer using the context)
Relevant Law: (cite specific sections/acts)
Next Steps: (practical advice)"""

OPENAI_SYSTEM = """You are a legal assistant specialized in Indian law including IPC, CrPC, Constitution, Consumer Protection Act, IT Act, Family Law, and Labour Law.

Always structure your response exactly like this:

**Short Answer:** (1-2 sentence answer)

**Explanation:** (detailed explanation)

**Relevant Law/Section:** (cite specific sections and acts)

**Next Steps:** (practical advice)

**Disclaimer:** This information is for educational purposes only and does not constitute legal advice. Please consult a qualified lawyer for advice specific to your situation.

Always cite specific sections. If context from legal documents is provided, use it."""


def _get_hf_pipeline():
    global _hf_pipeline
    if _hf_pipeline is None:
        from transformers import pipeline
        settings = get_settings()
        logger.info(f"Loading HuggingFace model: {settings.hf_model_name}")
        _hf_pipeline = pipeline(
            "text2text-generation",
            model=settings.hf_model_name,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.3,
        )
        logger.info("HuggingFace model loaded")
    return _hf_pipeline


def _build_context_text(context_chunks: list[dict]) -> str:
    if not context_chunks:
        return ""
    parts = []
    for chunk in context_chunks:
        source = chunk.get("source", "Unknown")
        text = chunk.get("text", "")
        parts.append(f"[{source}] {text}")
    return "\n\n".join(parts)


async def generate_response(query: str, context_chunks: list[dict], language: str = "en") -> dict:
    settings = get_settings()

    logger.info(f"Generating response for query: {query[:80]}...")
    logger.debug(f"Using {len(context_chunks)} context chunks")

    if settings.use_openai and settings.openai_api_key:
        return await _generate_openai(query, context_chunks, language)
    else:
        return _generate_context_based(query, context_chunks, language)


async def _generate_openai(query: str, context_chunks: list[dict], language: str) -> dict:
    from openai import AsyncOpenAI
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    context_text = _build_context_text(context_chunks)
    user_content = f"Context from legal documents:\n---\n{context_text}\n---\n\nQuestion: {query}" if context_text else f"Question: {query}"

    if language == "hi":
        user_content += "\n\nPlease respond in Hindi."

    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": OPENAI_SYSTEM},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
        max_tokens=1024,
    )

    raw_text = response.choices[0].message.content
    logger.info("OpenAI response received")
    return _parse_response(raw_text)


def _generate_context_based(query: str, context_chunks: list[dict], language: str) -> dict:
    """Build a structured response directly from RAG context.
    Uses the HF model for summarization, but falls back to
    context-based assembly if the model output is poor."""

    context_text = _build_context_text(context_chunks)

    if not context_text:
        return _no_context_response(query, language)

    # Try HF model with a simple prompt
    try:
        pipe = _get_hf_pipeline()
        simple_prompt = f"Answer this legal question using the context below.\n\nContext: {context_text[:1500]}\n\nQuestion: {query}\n\nAnswer:"
        result = pipe(simple_prompt)
        model_answer = result[0]["generated_text"].strip()
        logger.info(f"HF model output: {model_answer[:100]}...")
    except Exception as e:
        logger.warning(f"HF model failed: {e}")
        model_answer = ""

    # Check if model gave a real answer (not template echo or too short)
    model_usable = (
        len(model_answer) > 30
        and "[A brief" not in model_answer
        and "[1-2" not in model_answer
        and "sentence answer" not in model_answer.lower()
    )

    # Build structured response from context + model
    sources = list({c.get("source", "Unknown") for c in context_chunks})
    source_text = ", ".join(sources)

    # Extract the most relevant chunk
    best_chunk = context_chunks[0]["text"] if context_chunks else ""

    # Find law/section references in context
    law_refs = _extract_law_references(context_text)

    if model_usable:
        short_answer = model_answer[:200].split(". ")[0] + "."
        explanation = model_answer
    else:
        # Build answer from context directly
        short_answer = _build_short_answer(query, best_chunk)
        explanation = _build_explanation(context_chunks)

    next_steps = _build_next_steps(query)

    disclaimer = DISCLAIMER_HI if language == "hi" else DISCLAIMER

    full_answer = f"""**Short Answer:** {short_answer}

**Explanation:** {explanation}

**Relevant Law/Section:** {law_refs if law_refs else source_text}

**Next Steps:** {next_steps}

**Disclaimer:** {disclaimer}"""

    return {
        "answer": full_answer,
        "short_answer": short_answer,
        "explanation": explanation,
        "relevant_law": law_refs if law_refs else source_text,
        "next_steps": next_steps,
        "disclaimer": disclaimer,
    }


def _no_context_response(query: str, language: str) -> dict:
    disclaimer = DISCLAIMER_HI if language == "hi" else DISCLAIMER
    msg = f"I don't have specific legal documents about this query in my database yet. Please try rephrasing your question or consult a qualified lawyer for detailed advice on: {query}"
    full = f"**Short Answer:** {msg}\n\n**Disclaimer:** {disclaimer}"
    return {
        "answer": full,
        "short_answer": msg,
        "explanation": msg,
        "relevant_law": "Not available for this query",
        "next_steps": "Consult a qualified lawyer for specific legal advice.",
        "disclaimer": disclaimer,
    }


def _build_short_answer(query: str, best_chunk: str) -> str:
    """Build a concise answer from the best matching chunk."""
    # Take the first 2 sentences from the best chunk
    sentences = re.split(r'(?<=[.!?])\s+', best_chunk)
    short = " ".join(sentences[:2]).strip()
    if len(short) > 250:
        short = short[:247] + "..."
    return short


def _build_explanation(context_chunks: list[dict]) -> str:
    """Combine relevant chunks into a coherent explanation."""
    seen = set()
    parts = []
    for chunk in context_chunks[:4]:
        text = chunk["text"].strip()
        # Deduplicate
        key = text[:50]
        if key in seen:
            continue
        seen.add(key)
        source = chunk.get("source", "")
        parts.append(text)

    return "\n\n".join(parts)


def _extract_law_references(text: str) -> str:
    """Extract section/article references from text."""
    patterns = [
        r"(?:Section|Sec\.?)\s+\d+[A-Z]?(?:\s*(?:of|,)\s*(?:the\s+)?[\w\s]+(?:Act|Code|Constitution)[\w\s,]*(?:\d{4})?)?",
        r"Article\s+\d+[A-Z]?(?:\s*(?:of|,)\s*(?:the\s+)?[\w\s]+Constitution[\w\s]*)?",
        r"(?:IPC|CrPC|CPC|IT Act|BNSS|BNS)(?:\s*,?\s*\d{4})?",
    ]

    refs = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            cleaned = m.strip().rstrip(",").strip()
            if len(cleaned) > 5:
                refs.add(cleaned)

    if refs:
        return "; ".join(sorted(refs)[:8])
    return ""


def _build_next_steps(query: str) -> str:
    """Generate practical next steps based on query keywords."""
    query_lower = query.lower()

    if any(w in query_lower for w in ["fir", "complaint", "police", "report"]):
        return ("1) Visit the nearest police station with jurisdiction over the area where the incident occurred. "
                "2) Provide all details of the incident to the officer in charge. "
                "3) Get a copy of the FIR — it must be provided free of cost. "
                "4) If police refuse to file the FIR, send a written complaint to the Superintendent of Police or approach the Magistrate under Section 156(3) CrPC. "
                "5) You can also file a Zero FIR at any police station regardless of jurisdiction.")

    if any(w in query_lower for w in ["bail", "arrest", "detained"]):
        return ("1) Contact a criminal lawyer immediately. "
                "2) If the offence is bailable, bail is a matter of right — insist on it. "
                "3) For non-bailable offences, apply for bail before the appropriate court. "
                "4) For anticipatory bail, approach the Sessions Court or High Court under Section 438 CrPC. "
                "5) Ensure the arrested person is produced before a Magistrate within 24 hours.")

    if any(w in query_lower for w in ["divorce", "marriage", "maintenance", "alimony"]):
        return ("1) Consult a family law lawyer to understand your specific rights. "
                "2) Try mediation or counselling first if possible. "
                "3) File a petition in the Family Court having jurisdiction. "
                "4) Gather all relevant documents — marriage certificate, financial records, evidence of grounds for divorce. "
                "5) You may also seek interim maintenance during the proceedings under Section 24 of the Hindu Marriage Act.")

    if any(w in query_lower for w in ["consumer", "defective", "refund", "product"]):
        return ("1) First send a legal notice to the seller/service provider. "
                "2) File a consumer complaint online at edaakhil.nic.in or at the District Consumer Forum. "
                "3) Attach all bills, receipts, correspondence, and evidence. "
                "4) No court fee for claims up to Rs. 5 lakh. "
                "5) The complaint must be filed within 2 years of the cause of action.")

    if any(w in query_lower for w in ["cyber", "online", "hack", "fraud", "internet"]):
        return ("1) Report the cybercrime at cybercrime.gov.in (National Cyber Crime Reporting Portal). "
                "2) Call the helpline 1930 for immediate assistance. "
                "3) File an FIR at the local police station or cyber crime cell. "
                "4) Preserve all digital evidence — screenshots, emails, transaction records. "
                "5) Consult a lawyer specializing in cyber law.")

    if any(w in query_lower for w in ["fundamental", "rights", "constitution", "article"]):
        return ("1) Understand which specific fundamental right applies to your situation. "
                "2) If your rights are violated, you can file a writ petition under Article 32 (Supreme Court) or Article 226 (High Court). "
                "3) Consult a constitutional lawyer for guidance. "
                "4) You may also approach the National/State Human Rights Commission. "
                "5) Document all evidence of the rights violation.")

    if any(w in query_lower for w in ["workplace", "harassment", "posh", "employer", "salary"]):
        return ("1) Report the issue to the Internal Complaints Committee (ICC) if it's a harassment matter. "
                "2) File a complaint with the labour commissioner for wage/salary disputes. "
                "3) Consult a labour law lawyer. "
                "4) Gather all evidence — employment contracts, pay slips, correspondence. "
                "5) You may also approach the Labour Court or Industrial Tribunal.")

    # Default
    return ("1) Consult a qualified lawyer who specializes in the relevant area of law. "
            "2) Gather all relevant documents and evidence. "
            "3) Note down all dates, facts, and details of the matter. "
            "4) If it's urgent, you can also seek free legal aid through the District Legal Services Authority (DLSA). "
            "5) For immediate assistance, call the legal aid helpline or visit your nearest legal aid centre.")


def _parse_response(raw_text: str) -> dict:
    """Parse structured response from OpenAI output."""
    sections = {
        "short_answer": "",
        "explanation": "",
        "relevant_law": "",
        "next_steps": "",
        "disclaimer": DISCLAIMER,
    }

    patterns = {
        "short_answer": r"\*?\*?Short Answer\*?\*?:\s*(.*?)(?=\*?\*?Explanation|$)",
        "explanation": r"\*?\*?Explanation\*?\*?:\s*(.*?)(?=\*?\*?Relevant Law|$)",
        "relevant_law": r"\*?\*?Relevant Law[/\s]*Section\*?\*?:\s*(.*?)(?=\*?\*?Next Steps|$)",
        "next_steps": r"\*?\*?Next Steps\*?\*?:\s*(.*?)(?=\*?\*?Disclaimer|$)",
        "disclaimer": r"\*?\*?Disclaimer\*?\*?:\s*(.*?)$",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, raw_text, re.DOTALL | re.IGNORECASE)
        if match:
            sections[key] = match.group(1).strip()

    if not sections["short_answer"] and not sections["explanation"]:
        sections["explanation"] = raw_text.strip()
        sections["short_answer"] = raw_text.strip()[:200]

    return {
        "answer": raw_text.strip(),
        **sections,
    }
