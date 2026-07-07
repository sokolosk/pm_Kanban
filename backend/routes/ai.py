from fastapi import APIRouter, HTTPException, status

from ai import OpenRouterClient, OpenRouterError

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/test")
async def ai_connectivity_test() -> dict[str, str]:
    client = OpenRouterClient()
    try:
        result = await client.math_connectivity_test()
    except OpenRouterError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return {"result": result}
