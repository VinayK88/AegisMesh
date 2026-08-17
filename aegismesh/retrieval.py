from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class KnowledgeItem:
    id: str
    title: str
    text: str


CORPUS = [
    KnowledgeItem("kb-mfa", "Phishing-resistant authentication", "Phishing-resistant MFA reduces reliance on reusable credentials and weak interactive authentication."),
    KnowledgeItem("kb-token", "Token protection", "Token protection and continuous access evaluation can reduce replay value for stolen sessions."),
    KnowledgeItem("kb-oauth", "OAuth least privilege", "OAuth applications should request the minimum scopes required and high-impact consent should be governed."),
    KnowledgeItem("kb-jit", "Just-in-time privilege", "Standing administrative privilege can be reduced with time-bound elevation and isolated privileged workstations."),
    KnowledgeItem("kb-evidence", "Evidence-grounded investigation", "Security conclusions should preserve source identifiers, contradictory evidence, and the path from observation to conclusion."),
]


def retrieve(query: str, limit: int = 3) -> list[KnowledgeItem]:
    terms = {token.strip(".,:;()[]").lower() for token in query.split() if len(token) > 2}
    scored: list[tuple[int, KnowledgeItem]] = []
    for item in CORPUS:
        haystack = f"{item.title} {item.text}".lower()
        score = sum(1 for term in terms if term in haystack)
        scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], pair[1].id))
    return [item for score, item in scored[:limit] if score > 0] or CORPUS[:limit]
