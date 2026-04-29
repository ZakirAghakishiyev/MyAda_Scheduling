from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.user_ids import normalize_instructor_user_id
from app.db.session import get_db


def get_current_user_id(
    x_user_id: Annotated[str | None, Header(alias=settings.dev_user_id_header)] = None,
) -> str:
    if x_user_id is None or x_user_id.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing {settings.dev_user_id_header} (instructor user id header)",
        )
    try:
        return normalize_instructor_user_id(x_user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e


DbDep = Annotated[Session, Depends(get_db)]
UserIdDep = Annotated[str, Depends(get_current_user_id)]
