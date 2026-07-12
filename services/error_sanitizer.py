import re
from typing import Final


MAX_ERROR_MESSAGE_LENGTH: Final = 2000

SENSITIVE_PATTERNS: Final = (
    re.compile(
        r"(?i)(api[-_ ]?key)"
        r"\s*[:=]\s*['\"]?[^,\s'\"]+"
    ),
    re.compile(
        r"(?i)(access[-_ ]?token)"
        r"\s*[:=]\s*['\"]?[^,\s'\"]+"
    ),
    re.compile(
        r"(?i)(client[-_ ]?id)"
        r"\s*[:=]\s*['\"]?[^,\s'\"]+"
    ),
    re.compile(
        r"(?i)(password)"
        r"\s*[:=]\s*['\"]?[^,\s'\"]+"
    ),
    re.compile(
        r"(?i)(authorization)"
        r"\s*[:=]\s*['\"]?[^,\s'\"]+"
    ),
    re.compile(
        r"eyJ[A-Za-z0-9_-]+"
        r"\.[A-Za-z0-9_-]+"
        r"\.[A-Za-z0-9_-]+"
    ),
)


def sanitize_error_message(
    message: str,
) -> str:
    sanitized = str(message)

    for pattern in SENSITIVE_PATTERNS:
        sanitized = pattern.sub(
            lambda match: (
                f"{match.group(1)}=[REDACTED]"
                if match.lastindex
                else "[REDACTED]"
            ),
            sanitized,
        )

    sanitized = sanitized.strip()

    if not sanitized:
        sanitized = "No error message available."

    return sanitized[
        :MAX_ERROR_MESSAGE_LENGTH
    ]


def classify_retryable(
    error: Exception,
) -> bool:
    retryable_types = (
        TimeoutError,
        ConnectionError,
    )

    if isinstance(error, retryable_types):
        return True

    error_name = type(error).__name__.lower()
    message = str(error).lower()

    retryable_terms = (
        "timeout",
        "temporarily unavailable",
        "connection refused",
        "connection reset",
        "rate limit",
        "too many requests",
        "service unavailable",
        "gateway timeout",
    )

    return (
        "timeout" in error_name
        or any(
            term in message
            for term in retryable_terms
        )
    )
