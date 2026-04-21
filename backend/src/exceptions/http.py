from fastapi import HTTPException, status


class Unauthorized(HTTPException):
    def __init__(self, detail="Not authenticated"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class Forbidden(HTTPException):
    def __init__(self, detail="Forbidden"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class NotFound(HTTPException):
    def __init__(self, detail="Not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)
