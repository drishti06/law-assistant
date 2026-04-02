import re
from app.config import get_settings
from app.utils.logger import logger

_hf_pipeline = None

DISCLAIMER = "⚠️ This information is for educational purposes only and does not constitute legal advice. Please consult a qualified lawyer for advice specific to your situation."
DISCLAIMER_HI = "⚠️ यह जानकारी केवल शैक्षिक उद्देश्यों के लिए है और यह कानूनी सलाह नहीं है। अपनी स्थिति के लिए किसी योग्य वकील से परामर्श करें।"

OPENAI_SYSTEM = """You are a friendly legal assistant for Indian citizens. Users are common people who don't know legal terms.

Rules:
- Keep answers SHORT and to the point — no long paragraphs
- Use bullet points (•) everywhere instead of long sentences
- Explain in simple, everyday language (1 line per point max)
- When you mention a law/section, add a short bracket explanation
- Be empathetic but concise
- Use the provided legal context to give accurate information
- If the context doesn't cover the topic, say so honestly

Structure your response exactly like this:

**What This Means:**
• (1-2 bullet points summarizing their situation in simple words)

**Your Rights:**
• (bullet points — what the law says, keep each point to 1 line)

**What To Do Now:**
• (bullet point steps they can take — be specific and practical)

**Get Help:**
• (helplines, websites, offices — one per bullet)

**⚠️ Important:** This is general legal info, not legal advice. Consult a lawyer or your nearest DLSA for free legal help."""


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
    seen = set()
    for chunk in context_chunks:
        text = chunk.get("text", "").strip()
        key = text[:80]
        if key in seen:
            continue
        seen.add(key)
        source = chunk.get("source", "Unknown")
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
    user_content = f"Legal context from documents:\n---\n{context_text}\n---\n\nUser's problem: {query}" if context_text else f"User's problem: {query}"

    if language == "hi":
        user_content += "\n\nPlease respond in Hindi."

    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": OPENAI_SYSTEM},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
        max_tokens=512,
    )

    raw_text = response.choices[0].message.content
    logger.info("OpenAI response received")
    return _parse_response(raw_text)


def _generate_context_based(query: str, context_chunks: list[dict], language: str) -> dict:
    """Build a user-friendly structured response from RAG context."""

    context_text = _build_context_text(context_chunks)

    if not context_text:
        return _no_context_response(query, language)

    # Try HF model for a summary
    model_answer = _try_hf_summary(query, context_text)

    # Extract legal references from context
    law_refs = _extract_law_references(context_text)
    sources = list({c.get("source", "Unknown") for c in context_chunks})

    # Detect the legal topic from query + context
    topic = _detect_topic(query)

    # Build each section
    short_answer = _build_simple_answer(query, context_chunks, model_answer, topic)
    explanation = _build_plain_explanation(context_chunks, topic)
    relevant_law = _build_law_explanation(law_refs, context_text, topic)
    next_steps = _build_next_steps(query, topic)
    help_info = _build_help_info(topic)

    disclaimer = DISCLAIMER_HI if language == "hi" else DISCLAIMER

    full_answer = f"""**What This Means:**
• {short_answer}

**Your Rights:**
{explanation}

**Relevant Laws:**
{relevant_law}

**What To Do Now:**
{next_steps}

**Get Help:**
{help_info}

{disclaimer}"""

    return {
        "answer": full_answer,
        "short_answer": short_answer,
        "explanation": explanation,
        "relevant_law": relevant_law,
        "next_steps": next_steps,
        "disclaimer": disclaimer,
    }


def _try_hf_summary(query: str, context_text: str) -> str:
    """Try to get a summary from HF model. Returns empty string on failure."""
    try:
        pipe = _get_hf_pipeline()
        prompt = f"Summarize the legal answer for a common person.\n\nContext: {context_text[:1500]}\n\nQuestion: {query}\n\nSimple answer:"
        result = pipe(prompt)
        answer = result[0]["generated_text"].strip()

        # Validate output
        if (len(answer) > 30
                and "[A brief" not in answer
                and "[1-2" not in answer
                and "sentence answer" not in answer.lower()):
            logger.info(f"HF model output: {answer[:100]}...")
            return answer
    except Exception as e:
        logger.warning(f"HF model failed: {e}")
    return ""


def _detect_topic(query: str) -> str:
    """Detect the legal topic from a plain-language query."""
    q = query.lower()

    topic_keywords = {
        "rent": ["rent", "tenant", "landlord", "room", "eviction", "lease", "pg", "paying guest", "owner asking to leave", "vacate"],
        "theft": ["stole", "stolen", "theft", "robbery", "robbed", "snatched", "burglar", "break in"],
        "assault": ["beat", "beaten", "attack", "slap", "hit me", "punch", "hurt", "injured", "violence"],
        "cheating": ["cheated", "scam", "fraud", "fake", "deceived", "duped", "money taken"],
        "domestic": ["dowry", "domestic violence", "husband", "wife beating", "in-laws", "marital", "cruelty by husband"],
        "divorce": ["divorce", "separation", "marriage problem", "alimony", "maintenance"],
        "consumer": ["defective product", "refund", "consumer", "bad service", "warranty", "wrong product"],
        "cyber": ["online fraud", "hacked", "cyber", "internet", "social media", "online threat", "identity theft"],
        "employment": ["fired", "terminated", "salary not paid", "employer", "workplace", "harassment at work", "posh"],
        "accident": ["accident", "hit and run", "vehicle", "compensation", "injury claim"],
        "property": ["property", "land", "land dispute", "encroachment", "boundary", "title", "deed"],
        "fir": ["fir", "police", "complaint", "report crime"],
        "bail": ["bail", "arrest", "detained", "jail", "custody"],
        "fundamental": ["fundamental right", "constitution", "article", "discrimination", "freedom"],
        "neighbour": ["neighbour", "neighbor", "noise", "nuisance", "dispute with neighbor"],
    }

    for topic, keywords in topic_keywords.items():
        if any(kw in q for kw in keywords):
            return topic
    return "general"


def _build_simple_answer(query: str, context_chunks: list[dict], model_answer: str, topic: str) -> str:
    """Build a simple 2-3 sentence answer a common person can understand."""

    if model_answer:
        return model_answer[:300].rsplit(". ", 1)[0] + "."

    # Topic-based simple answers
    topic_answers = {
        "rent": "Your landlord cannot force you out before the agreement expires. They must follow legal process and give proper notice.",
        "theft": "Theft is a criminal offence. You can file an FIR at any police station — police are legally bound to register it.",
        "assault": "Physical attack is a criminal offence. You can file an FIR and claim compensation for injuries.",
        "cheating": "Fraud/cheating is a criminal offence. You can file a police complaint and a civil case to recover money.",
        "domestic": "Domestic violence is a serious criminal offence. The law protects victims with multiple remedies and immediate help.",
        "divorce": "You can get divorce through mutual consent or contested proceedings. You have rights to maintenance and custody.",
        "consumer": "You have strong consumer rights. File a complaint for defective products or bad service and claim compensation.",
        "cyber": "Cyber crimes are punishable under the IT Act. Report online at cybercrime.gov.in or call 1930.",
        "employment": "Labour laws protect you from unfair treatment. You can approach the Labour Commissioner or Labour Court.",
        "accident": "You have the right to claim compensation through the Motor Accident Claims Tribunal (MACT).",
        "property": "You have legal options to protect your property rights through civil courts.",
        "fir": "Filing an FIR is your legal right. Police must register it — if refused, you can escalate.",
        "bail": "Bail is a right for bailable offences. For non-bailable offences, apply through a lawyer in court.",
        "fundamental": "Your fundamental rights are guaranteed by the Constitution. You can approach courts if violated.",
        "neighbour": "Neighbour disputes can be resolved through police, local authorities, or courts depending on the issue.",
    }

    if topic in topic_answers:
        return topic_answers[topic]

    # Fallback: use best chunk but simplify
    if context_chunks:
        best = context_chunks[0]["text"]
        sentences = re.split(r'(?<=[.!?])\s+', best)
        return " ".join(sentences[:2]).strip()[:300]

    return "Based on Indian law, you have legal options available for your situation. Please see the details below."


def _build_plain_explanation(context_chunks: list[dict], topic: str) -> str:
    """Build a plain-language explanation from context chunks."""
    if not context_chunks:
        return "No specific legal provisions found in our documents for this query."

    seen = set()
    parts = []
    for chunk in context_chunks[:4]:
        text = chunk["text"].strip()
        key = text[:80]
        if key in seen:
            continue
        seen.add(key)
        source = chunk.get("source", "")

        # Clean up the text - remove excessive whitespace, page numbers etc.
        text = re.sub(r'\s+', ' ', text).strip()
        text = re.sub(r'Page \d+ of \d+', '', text).strip()

        if source:
            parts.append(f"According to **{source}**: {text}")
        else:
            parts.append(text)

    return "\n\n".join(parts)


def _build_law_explanation(law_refs: str, context_text: str, topic: str) -> str:
    """Explain the relevant laws in simple language."""

    # Map of common law references to simple explanations
    law_explanations = {
        "Transfer of Property Act": "This law governs how property (including rental property) is transferred and what rights tenants and landlords have",
        "Section 106": "This section says a landlord must give proper notice before asking a tenant to leave (15 days for monthly rent)",
        "Rent Control Act": "This state law protects tenants from unfair eviction and unreasonable rent increases",
        "Section 378": "This defines theft — when someone takes your property without your consent",
        "Section 379": "This prescribes punishment for theft — up to 3 years imprisonment and/or fine",
        "Section 420": "This deals with cheating and fraud — punishment up to 7 years imprisonment",
        "Section 498A": "This protects married women from cruelty by husband or in-laws — a serious criminal offence",
        "Section 323": "This deals with punishment for voluntarily causing hurt",
        "Section 324": "This deals with causing hurt using dangerous weapons",
        "Section 506": "This deals with criminal intimidation (threatening someone)",
        "IT Act": "The Information Technology Act, 2000 deals with cyber crimes and digital offences",
        "Consumer Protection Act": "This law protects buyers from defective products and poor services",
        "Motor Vehicles Act": "This law covers accidents, insurance claims, and compensation for injuries",
        "IPC": "Indian Penal Code — the main criminal law of India that defines crimes and punishments",
        "CrPC": "Code of Criminal Procedure — the law that explains how criminal cases are handled by police and courts",
        "BNS": "Bharatiya Nyaya Sanhita — the new criminal law that replaced the IPC from July 2024",
        "BNSS": "Bharatiya Nagarik Suraksha Sanhita — the new law that replaced CrPC from July 2024",
    }

    if not law_refs:
        return "Specific legal sections will be identified by a lawyer based on your exact situation."

    # Split refs and explain each
    refs = [r.strip() for r in law_refs.split(";")]
    explained = []
    for ref in refs:
        explanation = ""
        for law_key, law_desc in law_explanations.items():
            if law_key.lower() in ref.lower():
                explanation = law_desc
                break
        if explanation:
            explained.append(f"**{ref}** — {explanation}")
        else:
            explained.append(f"**{ref}**")

    return "\n".join(explained)


def _build_next_steps(query: str, topic: str) -> str:
    """Generate clear, numbered steps a common person can follow."""

    steps = {
        "rent": (
            "• **Don't leave immediately** — your agreement protects you\n"
            "• **Check your rent agreement** for end date & notice period\n"
            "• **Inform landlord in writing** that you have a valid agreement\n"
            "• **If threatened** — call police (100), illegal eviction is a crime\n"
            "• **Visit DLSA** for free legal aid if needed"
        ),
        "theft": (
            "• **File an FIR** at nearest police station with ID & evidence\n"
            "• **If police refuse** — ask for SHO, then write to SP\n"
            "• **Get a free copy** of the FIR\n"
            "• **Follow up** with the investigating officer"
        ),
        "assault": (
            "• **Get medical treatment first** — get MLC report from hospital\n"
            "• **File an FIR** with details & evidence (photos, CCTV, witnesses)\n"
            "• **If police refuse** — approach SP or Magistrate (Sec 156(3) CrPC)\n"
            "• **Consult a lawyer** for compensation claim"
        ),
        "cheating": (
            "• **Gather evidence** — messages, receipts, bank statements\n"
            "• **File an FIR** for cheating (Section 420 IPC)\n"
            "• **Online fraud?** Also report at cybercrime.gov.in\n"
            "• **Contact your bank** immediately to block transactions\n"
            "• **Send a legal notice** demanding money back"
        ),
        "domestic": (
            "• **In danger? Call 100 (police) or 181 (Women Helpline)** now\n"
            "• **File a complaint** at nearest police station\n"
            "• **File for Protection Order** under Domestic Violence Act\n"
            "• **You cannot be thrown out** of the shared household\n"
            "• **NCW Helpline:** 7827-170-170 for support & shelter"
        ),
        "divorce": (
            "• **Consult a family law lawyer** (many offer free first consultation)\n"
            "• **Try mediation/counselling** first if possible\n"
            "• **Gather documents** — marriage certificate, financial records\n"
            "• **File petition** in Family Court\n"
            "• **You can claim maintenance** during proceedings"
        ),
        "consumer": (
            "• **Keep all bills, receipts & warranty cards**\n"
            "• **Complain to seller/company** in writing first\n"
            "• **File complaint online** at edaakhil.nic.in (free up to Rs. 5 lakh)\n"
            "• **Must file within 2 years** of the problem"
        ),
        "cyber": (
            "• **Report at cybercrime.gov.in** or **call 1930**\n"
            "• **File an FIR** at police station or cyber crime cell\n"
            "• **Save all evidence** — screenshots, emails, transactions\n"
            "• **Contact bank immediately** if money was lost\n"
            "• **Change all passwords** if accounts compromised"
        ),
        "employment": (
            "• **Gather evidence** — offer letter, salary slips, emails\n"
            "• **Complain to employer/HR** in writing first\n"
            "• **File complaint** with Labour Commissioner\n"
            "• **For harassment** — report to ICC\n"
            "• **For unpaid salary** — approach Labour Court"
        ),
        "accident": (
            "• **Get medical treatment** & keep all hospital bills\n"
            "• **File an FIR** at nearest police station\n"
            "• **Note vehicle number, driver details & witnesses**\n"
            "• **File claim** with MACT (Motor Accident Claims Tribunal)\n"
            "• **Notify your insurance company** immediately"
        ),
        "fir": (
            "• **Go to any police station** (Zero FIR allowed)\n"
            "• **Give all details** clearly to the officer\n"
            "• **Get a free copy** of the FIR — your right\n"
            "• **If refused** — ask for SHO → write to SP → approach Magistrate"
        ),
        "bail": (
            "• **Contact a criminal lawyer** immediately\n"
            "• **Bailable offence** — bail is your right at police station\n"
            "• **Non-bailable** — lawyer applies in court\n"
            "• **Must be produced before Magistrate** within 24 hours\n"
            "• **Can't afford lawyer?** DLSA provides free legal aid"
        ),
    }

    if topic in steps:
        return steps[topic]

    # Default steps
    return (
        "• **Write down everything** — dates, names, what happened\n"
        "• **Gather evidence** — documents, photos, messages, witnesses\n"
        "• **Visit nearest DLSA** for free legal advice\n"
        "• **Consult a lawyer** — many offer free first consultations\n"
        "• **Don't delay** — many legal actions have time limits"
    )


def _build_help_info(topic: str) -> str:
    """Provide specific helplines and resources based on topic."""
    common = "**Free Legal Aid:** Visit your nearest District Legal Services Authority (DLSA) or call NALSA helpline."

    topic_help = {
        "domestic": (
            "- **Women Helpline:** 181 (24x7)\n"
            "- **Police:** 100\n"
            "- **NCW Helpline:** 7827-170-170\n"
            "- **One Stop Centre (Sakhi):** 181\n"
            f"- {common}"
        ),
        "cyber": (
            "- **Cyber Crime Portal:** cybercrime.gov.in\n"
            "- **Cyber Crime Helpline:** 1930\n"
            "- **Police:** 100\n"
            f"- {common}"
        ),
        "consumer": (
            "- **Consumer Helpline:** 1800-11-4000 (toll free)\n"
            "- **Online Complaint:** edaakhil.nic.in\n"
            "- **Consumer Forum:** Your district Consumer Disputes Redressal Forum\n"
            f"- {common}"
        ),
        "accident": (
            "- **Emergency:** 112\n"
            "- **Ambulance:** 108\n"
            "- **Police:** 100\n"
            "- **MACT:** Motor Accident Claims Tribunal in your district\n"
            f"- {common}"
        ),
    }

    if topic in topic_help:
        return topic_help[topic]

    return (
        f"- **Police:** 100\n"
        f"- **Emergency:** 112\n"
        f"- {common}\n"
        f"- **Legal Aid:** nalsa.gov.in"
    )


def _no_context_response(query: str, language: str) -> dict:
    disclaimer = DISCLAIMER_HI if language == "hi" else DISCLAIMER

    topic = _detect_topic(query)
    next_steps = _build_next_steps(query, topic)
    help_info = _build_help_info(topic)

    short = "I don't have specific documents for this yet, but here's what you can do."

    full = f"""**What This Means:**
• {short}

**What To Do Now:**
{next_steps}

**Get Help:**
{help_info}

{disclaimer}"""

    return {
        "answer": full,
        "short_answer": short,
        "explanation": "Specific legal provisions were not found in the available documents. Please consult a lawyer for detailed advice.",
        "relevant_law": "A lawyer will identify the exact laws applicable to your situation.",
        "next_steps": next_steps,
        "disclaimer": disclaimer,
    }


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
        "short_answer": r"\*?\*?(?:What This Means For You|Short Answer)\*?\*?:\s*(.*?)(?=\*?\*?(?:Your Rights|Explanation)|$)",
        "explanation": r"\*?\*?(?:Your Rights|Explanation)\*?\*?:\s*(.*?)(?=\*?\*?(?:Relevant Law|What You Should)|$)",
        "relevant_law": r"\*?\*?(?:Relevant Law[/\s]*Section|Relevant Laws)\*?\*?:\s*(.*?)(?=\*?\*?(?:Next Steps|What You Should)|$)",
        "next_steps": r"\*?\*?(?:Next Steps|What You Should Do Now)\*?\*?:\s*(.*?)(?=\*?\*?(?:Disclaimer|Where To Get|⚠️|Important)|$)",
        "disclaimer": r"\*?\*?(?:Disclaimer|⚠️ Important|Important)\*?\*?:?\s*(.*?)$",
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
