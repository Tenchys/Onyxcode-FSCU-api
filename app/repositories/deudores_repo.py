"""Repository for deudores morosos — exact RUT+DV lookup only."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class DeudorRecord:
    """Domain-relevant subset of a debtor record."""

    rut: int
    dv: str
    nombre: str  # Full name assembled from nombres + apellido_paterno + apellido_materno
    universidad: str | None
    monto_utm: float
    cod_universidad: int | None

    @classmethod
    def from_row(cls, row: Any) -> "DeudorRecord":
        """Build DeudorRecord from a SQLAlchemy Row object."""
        nombres = (row.nombres or "").strip()
        ap = (row.apellido_paterno or "").strip()
        am = (row.apellido_materno or "").strip()
        nombre_completo = f"{nombres} {ap} {am}".strip()
        monto = row.monto_utm
        if isinstance(monto, Decimal):
            monto = float(monto)
        return cls(
            rut=int(row.rut),
            dv=row.dv.strip().upper(),
            nombre=nombre_completo,
            universidad=row.universidad.strip() if row.universidad else None,
            monto_utm=monto,
            cod_universidad=row.cod_universidad,
        )


# Fixed SQL — no dynamic content, all via parameters
_EXACT_LOOKUP_SQL = text(
    """
    SELECT
        rut,
        dv,
        nombres,
        apellido_paterno,
        apellido_materno,
        monto_utm,
        cod_universidad,
        universidad
    FROM deudores_morosos
    WHERE rut = :rut AND dv = :dv
    LIMIT 1
    """
)


async def find_deudor_by_rut(session: AsyncSession, rut: int, dv: str) -> DeudorRecord | None:
    """Return the exact debtor record matching rut+dv, or None if not found.

    The query is fully parameterized — no string interpolation.
    Only the exact columns needed by the domain are selected.
    """
    result = await session.execute(
        _EXACT_LOOKUP_SQL,
        {"rut": str(rut), "dv": dv.strip().upper()},
    )
    row = result.mappings().first()
    if row is None:
        return None
    return DeudorRecord.from_row(row)
