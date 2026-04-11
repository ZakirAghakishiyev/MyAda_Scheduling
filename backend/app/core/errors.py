from fastapi import HTTPException, status


class NotFoundError(Exception):
    def __init__(self, message: str = "Resource not found"):
        self.message = message


class ConflictError(Exception):
    def __init__(self, message: str):
        self.message = message


class ValidationAppError(Exception):
    def __init__(self, message: str):
        self.message = message


class UpstreamError(Exception):
    def __init__(self, message: str):
        self.message = message


def http_not_found(exc: NotFoundError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=exc.message)


def http_conflict(exc: ConflictError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.message)


def http_validation(exc: ValidationAppError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message)
