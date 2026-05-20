import html
import re
from dataclasses import dataclass


INTERNAL_DOMAINS = {
    "internal.com",
    "mycompany.com",
    "company.com",
    "ourplatform.com",
    "github.com",
}

SPAM_KEYWORDS = {
    "boost your seo",
    "front page of google",
    "limited offer",
    "click here",
    "nigerian prince",
    "inheritance",
    "bank account details",
    "processing fee",
    "cold outreach",
    "quick question for the right person",
    "collab opportunity",
}

SECURITY_KEYWORDS = {
    "ransomware",
    "exfiltrated",
    "publish the data",
    "dark web",
    "btc",
    "bitcoin",
    "suspicious login",
    "unknown location",
    "valid credentials",
    "data breach",
    "pay now",
}

LEGAL_KEYWORDS = {
    "legal action",
    "legal team",
    "cease and desist",
    "formal correspondence",
    "gdpr",
    "article 20",
    "statutory",
    "trademark",
    "right to portability",
}

URGENCY_KEYWORDS = {
    "urgent",
    "p0",
    "production down",
    "immediately",
    "critical",
    "within 24 hours",
    "within the next hour",
    "deadline",
    "mission-critical",
    "legal",
    "ransomware",
}

BILLING_KEYWORDS = {
    "refund",
    "invoice",
    "billing",
    "payment",
    "subscription",
    "renewal",
    "credit",
    "pro-rata",
    "prorated",
}

BUG_KEYWORDS = {
    "bug",
    "crash",
    "server error",
    "500",
    "403",
    "not working",
    "broken",
    "failing",
    "missing",
    "data missing",
    "silently",
}

COMPLIANCE_KEYWORDS = {
    "hipaa",
    "baa",
    "soc 2",
    "iso 27001",
    "compliance",
    "gdpr",
    "data residency",
    "dpa",
}

FEATURE_KEYWORDS = {
    "feature request",
    "roadmap",
    "dark mode",
    "custom branding",
    "ios app",
    "rate limit increase",
}

COMPLAINT_KEYWORDS = {
    "unhappy",
    "angry",
    "worst",
    "still no reply",
    "no reply",
    "unacceptable",
    "cancel",
    "churn",
    "public review",
    "trustpilot",
    "g2",
    "capterra",
    "twitter",
}


@dataclass
class HeuristicResult:
    category: str
    urgency: str
    priority_score: int
    requires_human: bool
    status: str
    flags: dict


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""

    decoded = html.unescape(value)
    decoded = re.sub(r"<[^>]+>", " ", decoded)
    decoded = re.sub(r"\s+", " ", decoded)
    return decoded.strip()


def get_domain(email: str) -> str:
    if "@" not in email:
        return ""
    return email.split("@", 1)[1].lower().strip()


def contains_any(text: str, keywords: set[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def calculate_priority(
    category: str,
    urgency: str,
    flags: dict,
) -> int:
    score = 0

    if urgency == "Critical":
        score += 90
    elif urgency == "High":
        score += 70
    elif urgency == "Medium":
        score += 40
    else:
        score += 10

    if flags.get("security_flag"):
        score += 40

    if flags.get("legal_flag"):
        score += 35

    if flags.get("complaint_flag"):
        score += 20

    if category in {"Legal", "Compliance", "Bug Report"}:
        score += 15

    if flags.get("spam_flag"):
        score = min(score, 5)

    if flags.get("internal_flag"):
        score = min(score, 15)

    return min(score, 100)


def run_heuristic_triage(
    sender: str,
    subject: str | None,
    body: str | None,
) -> HeuristicResult:
    clean_subject = normalize_text(subject)
    clean_body = normalize_text(body)
    combined_text = f"{clean_subject} {clean_body}".strip()
    lowered = combined_text.lower()

    domain = get_domain(sender)

    flags = {
        "empty_subject": len(clean_subject) == 0,
        "empty_body": len(clean_body) == 0,
        "body_truncated": False,
        "spam_flag": False,
        "internal_flag": False,
        "security_flag": False,
        "legal_flag": False,
        "urgency_flag": False,
        "complaint_flag": False,
        "billing_flag": False,
        "bug_flag": False,
        "compliance_flag": False,
        "feature_flag": False,
    }

    if len(clean_body) > 10_000:
        flags["body_truncated"] = True

    is_internal = domain in INTERNAL_DOMAINS
    is_spam = contains_any(lowered, SPAM_KEYWORDS)
    is_security = contains_any(lowered, SECURITY_KEYWORDS)
    is_legal = contains_any(lowered, LEGAL_KEYWORDS)
    is_urgent = contains_any(lowered, URGENCY_KEYWORDS)
    is_billing = contains_any(lowered, BILLING_KEYWORDS)
    is_bug = contains_any(lowered, BUG_KEYWORDS)
    is_compliance = contains_any(lowered, COMPLIANCE_KEYWORDS)
    is_feature = contains_any(lowered, FEATURE_KEYWORDS)
    is_complaint = contains_any(lowered, COMPLAINT_KEYWORDS)

    flags["internal_flag"] = is_internal
    flags["spam_flag"] = is_spam
    flags["security_flag"] = is_security
    flags["legal_flag"] = is_legal
    flags["urgency_flag"] = is_urgent
    flags["billing_flag"] = is_billing
    flags["bug_flag"] = is_bug
    flags["compliance_flag"] = is_compliance
    flags["feature_flag"] = is_feature
    flags["complaint_flag"] = is_complaint

    category = "Other"
    urgency = "Low"
    requires_human = False
    status = "Received"

    if is_internal:
        category = "Internal"
        urgency = "Low"
        status = "Ignored"
        requires_human = False

    elif is_spam:
        category = "Spam"
        urgency = "Low"
        status = "Ignored"
        requires_human = False

    elif is_security:
        category = "Legal" if is_legal else "Other"
        urgency = "Critical"
        status = "Escalated"
        requires_human = True

    elif is_legal:
        category = "Legal"
        urgency = "Critical"
        status = "Escalated"
        requires_human = True

    elif is_compliance:
        category = "Compliance"
        urgency = "High" if is_urgent else "Medium"
        status = "Escalated" if is_urgent else "Received"
        requires_human = is_urgent

    elif is_bug:
        category = "Bug Report"
        urgency = "High" if is_urgent else "Medium"
        requires_human = is_urgent

    elif is_complaint:
        category = "Complaint"
        urgency = "High" if is_urgent else "Medium"
        requires_human = True

    elif is_billing:
        category = "Billing"
        urgency = "Medium"
        requires_human = False

    elif is_feature:
        category = "Feature Request"
        urgency = "Low"
        requires_human = False

    elif "pricing" in lowered or "discount" in lowered or "plan" in lowered:
        category = "Inquiry"
        urgency = "Medium"
        requires_human = False

    if is_urgent and urgency not in {"Critical", "High"}:
        urgency = "High"

    priority_score = calculate_priority(category, urgency, flags)

    return HeuristicResult(
        category=category,
        urgency=urgency,
        priority_score=priority_score,
        requires_human=requires_human,
        status=status,
        flags=flags,
    )