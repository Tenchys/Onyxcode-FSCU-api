"""RUT query response schema."""
from pydantic import BaseModel, ConfigDict, Field


class DeudaResponse(BaseModel):
    """Schema for a RUT lookup response."""

    found: bool = Field(description="Whether the RUT was found in the database.")
    rut: int = Field(description="Normalized RUT number (without DV).")
    dv: str = Field(description="Verifier digit (uppercase).")
    nombre: str | None = Field(default=None, description=" Debtor full name.")
    universidad: str | None = Field(default=None, description="Associated university.")
    monto_utm: float | None = Field(default=None, description="Debt amount in UTM.")
    monto_clp: float | None = Field(default=None, description="Debt amount in CLP.")
    utm_fecha: str | None = Field(default=None, description="UTM reference date (YYYY-MM).")

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "found": True,
                "rut": 12345678,
                "dv": "5",
                "nombre": "Juan Pérez",
                "universidad": "Universidad de Chile",
                "monto_utm": 150.5,
                "monto_clp": 11460500,
                "utm_fecha": "2025-03",
            }
        },
    )
