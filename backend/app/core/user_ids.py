"""Normalize instructor user ids to canonical UUID strings for storage and APIs."""

from __future__ import annotations

from uuid import NAMESPACE_OID, UUID, uuid5

# Deterministic UUIDs for legacy integer instructor keys (mock CSVs, pre-GUID Attendance rows).
LEGACY_INSTRUCTOR_USER_ID_NAMESPACE = uuid5(NAMESPACE_OID, "scheduling-ai.instructor-user-id")

def normalize_instructor_user_id(value: str | int) -> str:
    """
    Return a canonical UUID string: Auth-style UUIDs are normalized; legacy numeric ids map
    deterministically so existing varchar/integer keys migrate to the same stored GUID.
    """
    if isinstance(value, int):
        return str(uuid5(LEGACY_INSTRUCTOR_USER_ID_NAMESPACE, f"legacy-instructor:{value}"))
    s = str(value).strip()
    if not s:
        raise ValueError("Instructor user id is empty")
    try:
        return str(UUID(s))
    except ValueError:
        if s.isdigit():
            return str(uuid5(LEGACY_INSTRUCTOR_USER_ID_NAMESPACE, f"legacy-instructor:{s}"))
        raise ValueError(
            "Instructor user id must be a UUID or legacy numeric instructor key"
        ) from None
