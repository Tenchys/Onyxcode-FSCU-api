"""RUT lookup endpoint."""
from fastapi import APIRouter, HTTPException, Path

from app.api.v1.schemas_rut import DeudaResponse
from app.domain.rut import parse_rut

router = APIRouter(tags=["rut"])


@router.get(
    "/rut/{rut}",
    response_model=DeudaResponse,
    responses={
        400: {"description": "Invalid RUT format or verifier digit mismatch."},
    },
)
def lookup_rut(
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

    # TODO: F03 — integrate repository to fetch real data
    # Placeholder response until repository is implemented
    return DeudaResponse(
        found=False,
        rut=rut_info.rut,
        dv=rut_info.dv,
    )
