from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="Healthcheck")
async def health() -> dict:
    return {"status": "ok"}