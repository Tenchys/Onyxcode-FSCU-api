"""RUT lookup orchestration service."""
from dataclasses import dataclass

from app.db.postgres import get_db_session
from app.repositories.deudores_repo import DeudorRecord, find_deudor_by_rut


class DeudorNotFoundError(Exception):
    """Raised when no debtor matches the given RUT."""


class DatabaseError(Exception):
    """Raised on infrastructure failures (timeout, connection, etc.)."""


@dataclass(frozen=True)
class LookupResult:
    """Result of a RUT lookup operation."""

    found: bool
    rut: int
    dv: str
    nombre: str | None = None
    universidad: str | None = None
    monto_utm: float | None = None
    cod_universidad: int | None = None


async def lookup_rut(rut: int, dv: str) -> LookupResult:
    """Look up an exact RUT+DV in the deudores table.

    Returns LookupResult with found=True and debtor data if present.
    Returns LookupResult with found=False if no record matches.
    Raises DatabaseError on infrastructure failures.
    """
    try:
        async with get_db_session() as session:
            record: DeudorRecord | None = await find_deudor_by_rut(session, rut, dv)
    except Exception as exc:
        raise DatabaseError(f"Database error during lookup: {exc}") from exc

    if record is None:
        return LookupResult(found=False, rut=rut, dv=dv)

    return LookupResult(
        found=True,
        rut=record.rut,
        dv=record.dv,
        nombre=record.nombre,
        universidad=record.universidad,
        monto_utm=record.monto_utm,
        cod_universidad=record.cod_universidad,
    )
