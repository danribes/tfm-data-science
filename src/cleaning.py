"""Parse and clean raw INE JSON into tidy DataFrames."""

import pandas as pd


def _parse_trimestre(ts_ms: int) -> str:
    """Convert INE epoch-ms to 'YYYY-QN' string."""
    t = pd.Timestamp(ts_ms, unit="ms")
    q = (t.month - 1) // 3 + 1
    return f"{t.year}-Q{q}"


# ---------------------------------------------------------------------------
# IPV
# ---------------------------------------------------------------------------

def parse_ipv_anual(data: list[dict]) -> pd.DataFrame:
    """
    Flatten IPV annual CCAA table (49300).
    Columns: ccaa, tipo_vivienda, metrica, anyo, valor
    """
    # Format: "Andalucía. Media anual. Vivienda nueva. " (trailing space after last dot)
    rows = []
    for series in data:
        nombre = series.get("Nombre", "")
        parts = [p.strip() for p in nombre.split(".") if p.strip()]
        if len(parts) < 3:
            continue
        ccaa, metrica, tipo = parts[0], parts[1], parts[2]
        for obs in series.get("Data", []):
            if obs.get("Secreto") or obs.get("Valor") is None:
                continue
            rows.append({
                "ccaa": ccaa,
                "metrica": metrica,
                "tipo_vivienda": tipo,
                "anyo": obs["Anyo"],
                "valor": obs["Valor"],
            })
    return pd.DataFrame(rows)


def parse_ipv_trimestral(data: list[dict]) -> pd.DataFrame:
    """
    Flatten IPV quarterly CCAA table (76201).
    Columns: ccaa, tipo_vivienda, metrica, trimestre, anyo, valor
    """
    rows = []
    for series in data:
        nombre = series.get("Nombre", "")
        for obs in series.get("Data", []):
            if obs.get("Secreto") or obs.get("Valor") is None:
                continue
            rows.append({
                "nombre_serie": nombre,
                "trimestre": _parse_trimestre(obs["Fecha"]),
                "anyo": obs["Anyo"],
                "valor": obs["Valor"],
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# IPC
# ---------------------------------------------------------------------------

def parse_ipc_ccaa(data: list[dict]) -> pd.DataFrame:
    """
    Flatten IPC by CCAA table (76136).
    Keeps only 'Índice general' series for simplicity.
    Columns: ccaa, anyo, mes, valor
    """
    rows = []
    for series in data:
        nombre = series.get("Nombre", "")
        if "Índice general" not in nombre:
            continue
        # Extract CCAA name: first segment before first dot
        ccaa = nombre.split(".")[0].strip()
        for obs in series.get("Data", []):
            if obs.get("Secreto") or obs.get("Valor") is None:
                continue
            ts = pd.Timestamp(obs["Fecha"], unit="ms")
            rows.append({
                "ccaa": ccaa,
                "anyo": ts.year,
                "mes": ts.month,
                "valor": obs["Valor"],
            })
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    # Annual mean per CCAA — explicit cast needed due to pandas-stubs gap
    result: pd.DataFrame = df.groupby(["ccaa", "anyo"], as_index=False).agg(  # type: ignore[assignment]
        ipc_media_anual=("valor", "mean")
    )
    return result


# ---------------------------------------------------------------------------
# Salarios
# ---------------------------------------------------------------------------

def parse_salario_ccaa(data: list[dict]) -> pd.DataFrame:
    """
    Flatten salary table (28191): media bruta anual por CCAA.
    Keeps 'Ambos sexos' + 'Media' rows only.
    Columns: ccaa, anyo, salario_medio_anual
    """
    rows = []
    for series in data:
        nombre = series.get("Nombre", "")
        if "Ambos sexos" not in nombre or "Media." not in nombre:
            continue
        # Extract CCAA: middle segment
        parts = [p.strip() for p in nombre.split(".")]
        # Format: "Ambos sexos. <CCAA>. Dato base. Media."
        if len(parts) < 4:
            continue
        ccaa = parts[1]
        for obs in series.get("Data", []):
            if obs.get("Secreto") or obs.get("Valor") is None:
                continue
            rows.append({
                "ccaa": ccaa,
                "anyo": obs["Anyo"],
                "salario_medio_anual": obs["Valor"],
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Asequibilidad (join)
# ---------------------------------------------------------------------------

def build_asequibilidad(ipv: pd.DataFrame, salario: pd.DataFrame) -> pd.DataFrame:
    """
    Join IPV (general index) with salary to compute affordability ratio.
    ratio = IPV_index / (salario / salario_base_2007)
    Uses base year 2015 = 100 (INE convention for IPV).
    Returns: ccaa, anyo, ipv_general, salario_medio, ratio_asequibilidad
    """
    ipv_gen = ipv[(ipv["tipo_vivienda"] == "General") & (ipv["metrica"] == "Media anual")].copy()  # type: ignore[assignment]
    ipv_gen = ipv_gen.rename(columns={"valor": "ipv_general"})[["ccaa", "anyo", "ipv_general"]]  # type: ignore[call-overload]

    merged = ipv_gen.merge(salario, on=["ccaa", "anyo"], how="inner")

    # Normalise salary to base year 2015 (index: actual / 2015_value * 100)
    base = merged[merged["anyo"] == 2015].set_index("ccaa")["salario_medio_anual"]
    merged["salario_idx"] = merged.apply(
        lambda r: (r["salario_medio_anual"] / base.get(r["ccaa"], float("nan"))) * 100,
        axis=1,
    )
    merged["ratio_asequibilidad"] = merged["ipv_general"] / merged["salario_idx"]
    return merged.dropna(subset=["ratio_asequibilidad"]).sort_values(["ccaa", "anyo"])
