from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, status

from ai import OpenRouterClient, OpenRouterError

router = APIRouter(prefix="/api/ai", tags=["ai"])

AI_CLIENT_FACTORY: Callable[[], OpenRouterClient] = OpenRouterClient


def get_ai_client() -> OpenRouterClient:
    return AI_CLIENT_FACTORY()


@router.post("/test")
async def ai_connectivity_test(
    client: OpenRouterClient = Depends(get_ai_client),
) -> dict[str, str]:
    try:
        result = await client.math_connectivity_test()
    except OpenRouterError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return {"result": result}
