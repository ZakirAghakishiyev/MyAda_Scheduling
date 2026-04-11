from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db


def get_current_user_id(
    x_user_id: Annotated[str | None, Header(alias=settings.dev_user_id_header)] = None,
) -> int:
    if x_user_id is None or x_user_id.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing {settings.dev_user_id_header} (dev auth: set instructor user id)",
        )
    try:
        return int(x_user_id.strip())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user id header",
        ) from e


DbDep = Annotated[Session, Depends(get_db)]
UserIdDep = Annotated[int, Depends(get_current_user_id)]
