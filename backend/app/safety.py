import re
from typing import ClassVar

from pydantic import BaseModel, Field

from .models import FieldServiceReport


class SafetyAnalysis(BaseModel):
    report_id: str = Field(..., description="The unique identifier for the field service report.")
    contains_personal_information: bool = Field(..., description="Indicates whether the report contains personal information.")
    contains_physical_security_information: bool = Field(..., description="Indicates whether the report contains physical security information.")
    contains_technical_information: bool = Field(..., description="Indicates whether the report contains technical information.")
    warnings: list[str] = Field(..., description="A list of warnings generated during the safety analysis.")

    EMAIL_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
    PHONE_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")
    SECURITY_CODE_PATTERNS: ClassVar[list[re.Pattern[str]]] = [
        re.compile(r"\b(?:access|entry|security|alarm|door|gate|site)\s+(?:code|pin|number)\b", re.IGNORECASE),
        re.compile(r"\b(?:plant(?:[- ]?room)|key(?:[- ]?location)?|spare\s+key)\b", re.IGNORECASE),
        re.compile(r"\b(?:plant(?:[- ]?room)?\s+access\s+(?:code|pin|number)|door\s+(?:code|pin|number)|alarm\s+(?:code|pin|number))\b", re.IGNORECASE),
    ]
    TECHNICIAN_ID_PATTERN: ClassVar[re.Pattern[str]] = re.compile(r"\bT-\d+\b", re.IGNORECASE)
    PERSONAL_NAME_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(?:site contact|facilities manager|manager|contact|engineer)\s+(?:is|was|:)?\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+",
    )
    ADDRESS_PATTERN: ClassVar[re.Pattern[str]] = re.compile(
        r"\b(?:home|personal)\s+address\b|\b\d{1,5}\s+[A-Z][A-Za-z]+\s+(?:Lane|Road|Street|Court|Drive|Avenue|Way|Close|Place|Road|Rd|St|Ave)\b"
    )

    @classmethod
    def detect_physical_security_information(cls, text: str) -> bool:
        """Detect category-level access and physical-security language in untrusted text."""
        for pattern in cls.SECURITY_CODE_PATTERNS:
            if pattern.search(text):
                return True
        return False

    @classmethod
    def contains_personal_data(cls, text: str) -> bool:
        """Detect contact, name, or address categories without relying on sample values."""
        return bool(
            cls.EMAIL_PATTERN.search(text)
            or cls.PHONE_PATTERN.search(text)
            or cls.PERSONAL_NAME_PATTERN.search(text)
            or cls.ADDRESS_PATTERN.search(text)
        )

    @classmethod
    def from_report(cls, report: FieldServiceReport) -> "SafetyAnalysis":
        """Create operator-only safety flags without copying sensitive source text."""
        text = " ".join([report.asset, report.resolution, report.technician_notes])

        warnings: list[str] = []

        contains_personal_information = bool(
            cls.contains_personal_data(text)
        )
        contains_physical_security_information = cls.detect_physical_security_information(text)
        contains_technical_information = bool(report.technician_id or cls.TECHNICIAN_ID_PATTERN.search(text))

        if contains_personal_information:
            warnings.append("Personal contact information detected.")
        if contains_physical_security_information:
            warnings.append("Physical security information detected.")
        if contains_technical_information:
            warnings.append("Technical/internal identifier detected.")

        return cls(
            report_id=report.report_id,
            contains_personal_information=contains_personal_information,
            contains_physical_security_information=contains_physical_security_information,
            contains_technical_information=contains_technical_information,
            warnings=warnings,
        )


def analyze_safety(report: FieldServiceReport) -> SafetyAnalysis:
    """Analyze one report for personal, physical-security, and internal identifier risks."""
    return SafetyAnalysis.from_report(report)


RECOMMENDATION_WORDS = re.compile(
    r"\b(?:recommend|recommended|should|follow[- ]?up|monitor|review|next visit|outstanding)\b",
    re.IGNORECASE,
)

INSTRUCTION_WORDS = re.compile(
    r"\b(?:ignore|publish|suppress|omit|summary tool|previous instructions|instruction)\b",
    re.IGNORECASE,
)


def _split_sentences(notes: str) -> list[str]:
    """Split free-text notes into sentence-level candidates for category-based selection."""
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", notes.strip())
        if sentence.strip()
    ]


def _is_safe_sentence(sentence: str) -> bool:
    """Reject sentences with embedded instructions or personal/physical-security content."""
    if INSTRUCTION_WORDS.search(sentence):
        return False
    if SafetyAnalysis.contains_personal_data(sentence) or SafetyAnalysis.detect_physical_security_information(sentence):
        return False
    return True


def extract_safe_recommendations(notes: str) -> str:
    """Keep recommendation-bearing sentences while excluding untrusted details."""
    selected = [
        sentence
        for sentence in _split_sentences(notes)
        if RECOMMENDATION_WORDS.search(sentence) and _is_safe_sentence(sentence)
    ]
    return " ".join(selected)


def extract_safe_findings(notes: str) -> str:
    """Keep observation/diagnostic sentences describing what was found during the visit.

    Recommendation-bearing sentences are excluded here so they are only published once,
    under outstanding/recommended work, rather than duplicated into findings.
    """
    selected = [
        sentence
        for sentence in _split_sentences(notes)
        if not RECOMMENDATION_WORDS.search(sentence) and _is_safe_sentence(sentence)
    ]
    return " ".join(selected)
