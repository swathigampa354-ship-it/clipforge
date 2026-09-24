# Common response schemas
from pydantic import BaseModel, Field
from typing import Generic, TypeVar, Optional, Any

T = TypeVar('T')


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None
    error: Optional[str] = None

    class Config:
        json_schema_mode_override = "validation"


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    limit: int
    total_pages: int

    class Config:
        json_schema_mode_override = "validation"


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[list[str]] = None
    code: Optional[str] = None

    class Config:
        json_schema_mode_override = "validation"
