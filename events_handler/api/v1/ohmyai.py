from fastapi import APIRouter, Depends

from core.base_orjson_model import BaseORJSONModel
from core.settings import get_settings

router = APIRouter()

settings = get_settings()


class Event(BaseORJSONModel):
    username: str | None = None
    payload: str | None = None
    phone: int | None = None


@router.post(
    path="/workshow_register",
    summary="Регистрация на Workshow",
    description="Регистрация на Workshow"
)
async def workshow_register(event: Event = Depends()) -> dict:
    return {"status": "ok"}
