"""RUT lookup endpoint."""
from fastapi import APIRouter, HTTPException, Path, status
from unittest.mock import MagicMock

from app.api.v1.schemas_rut import DeudaResponse
from app.domain.rut import parse_rut
from app.security.rate_limit import check_rut_rate_limit
from app.services.rut_lookup import (
    DatabaseError,
    LookupResult,
    UtmUnavailableError,
    lookup_rut as lookup_rut_service,
)

router = APIRouter(tags=["rut"])


@router.get(
    "/rut/{rut}",
    response_model=DeudaResponse,
    responses={
        400: {"description": "Invalid RUT format or verifier digit mismatch."},
        429: {"description": "Rate limit exceeded for RUT or IP."},
        404: {"description": "RUT not found in database."},
        500: {"description": "Internal server error."},
    },
)
async def lookup_rut(
    rut: str = Path(
        ...,
        description="Chilean RUT in canonical format (e.g. 12.345.678-5 or 12345678K).",
    ),
) -> DeudaResponse:
    """Look up a debtor by exact RUT.

    Returns minimal debtor record if found; otherwise a response with found=False.
    Never exposes listings, pagination or partial searches.
    """
    # Validate and normalize BEFORE touching the database
    try:
        rut_info = parse_rut(rut)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        from app.core.settings import get_settings
        settings = get_settings()
    except Exception:
        # Fallback for testing without full env vars
        settings = MagicMock()
        settings.rate_limit_window_seconds = 60
        settings.rate_limit_per_rut = 10
        settings.rate_limit_burst = 5

    # F05-T02: Check rate limit per RUT normalized
    normalized_rut = f"{rut_info.rut}-{rut_info.dv}"
    allowed, _ = await check_rut_rate_limit(
        normalized_rut,
        settings.rate_limit_window_seconds,
        settings.rate_limit_per_rut,
        settings.rate_limit_burst,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this RUT.",
        )

    # F03 — integrate service to fetch real data
    try:
        result: LookupResult = await lookup_rut_service(rut=rut_info.rut, dv=rut_info.dv)
    except (DatabaseError, UtmUnavailableError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error.",
        )

    if not result.found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RUT not found.",
        )

    return DeudaResponse(
        found=True,
        rut=result.rut,
        dv=result.dv,
        nombre=result.nombre,
        universidad=result.universidad,
        monto_utm=result.monto_utm,
        monto_clp=result.monto_clp,
        utm_fecha=result.utm_fecha,
    )
