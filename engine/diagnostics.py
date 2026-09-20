"""Interpretation limits detected in computed scenario outputs."""
from collections.abc import Iterable

NEGATIVE_DEBT_NOTE = (
    "La trayectoria alcanza deuda negativa: queda fuera del dominio de deuda "
    "bruta de este modelo. No se modelan la acumulación de activos ni la "
    "respuesta de política al agotar la deuda."
)


def debt_domain_warnings(values: Iterable[float]) -> list[str]:
    return [NEGATIVE_DEBT_NOTE] if any(value < 0 for value in values) else []
