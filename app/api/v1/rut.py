"""RUT lookup endpoint."""
from fastapi import APIRouter, HTTPException, Path, status

from app.api.v1.schemas_rut import DeudaResponse
from app.domain.rut import parse_rut
from app.services.rut_lookup import DatabaseError, LookupResult, lookup_rut as lookup_rut_service

router = APIRouter(tags=["rut"])


@router.get(
    "/rut/{rut}",
    response_model=DeudaResponse,
    responses={
        400: {"description": "Invalid RUT format or verifier digit mismatch."},
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

    # F03 — integrate service to fetch real data
    try:
        result: LookupResult = await lookup_rut_service(rut=rut_info.rut, dv=rut_info.dv)
    except DatabaseError:
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
    )
