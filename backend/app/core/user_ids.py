"""Normalize instructor / actor user ids (Auth GUIDs or legacy numeric strings)."""

from __future__ import annotations

from uuid import UUID


def normalize_instructor_user_id(value: str | int) -> str:
    """
    Accept Auth-style UUID strings (canonicalized) or legacy integer ids from mock/Attendance.
    """
    if isinstance(value, int):
        return str(value)
    s = str(value).strip()
    if not s:
        raise ValueError("Instructor user id is empty")
    try:
        return str(UUID(s))
    except ValueError:
        if s.isdigit():
            return s
        raise ValueError("Instructor user id must be a UUID or numeric string") from None
