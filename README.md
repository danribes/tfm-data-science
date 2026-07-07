# Asequibilidad de Vivienda Regional en España

Repositorio del **Trabajo de Fin de Máster** (Evolve — Máster en Data Science). Pipeline ETL + análisis de asequibilidad de vivienda por comunidad autónoma.

**Entregas del curso:** [docs/entregas/](docs/entregas/) — [01 Ideas de producto](docs/entregas/01_ideas_producto.md) · [02 Selección de idea y datos necesarios](docs/entregas/02_datos_necesarios.md)

**Fuente:** API pública del INE (sin autenticación)  
**Periodo:** 2007–2025  
**Granularidad:** CCAA (17 comunidades autónomas)

## Instalación

```bash
pip install -r requirements.txt
```

## Uso rápido

```bash
# Descarga todas las series y genera CSVs procesados
python fetch_data.py

# Solo últimos 5 periodos (prueba rápida)
python fetch_data.py --nult 5

# Reprocesar sin volver a descargar
python fetch_data.py --cache
```

## Estructura

```
docs/entregas/       Entregables del máster (01_ideas, 02_datos)
data/raw/            JSON crudo descargado de la API INE
data/processed/      CSVs limpios: ipv, ipc, salario, asequibilidad
notebooks/           Análisis exploratorio
src/
  config.py          Rutas y tabla IDs
  client.py          Cliente API INE
  cleaning.py        Parsers JSON → DataFrame
charts/              Gráficos exportados
```

## Tablas INE utilizadas

| ID | Operación | Contenido |
|---|---|---|
| 49300 | IPV | Índice precios vivienda por CCAA, anual |
| 76201 | IPV | Índice precios vivienda por CCAA, trimestral |
| 76136 | IPC | IPC general por CCAA |
| 28191 | Salarios | Salario bruto anual medio y percentiles por CCAA |

## Índice de asequibilidad

```
ratio_asequibilidad = IPV_index_ccaa / salario_index_ccaa

donde salario_index = (salario_anual / salario_2015) × 100
```

Un ratio > 1 indica que los precios suben más rápido que los salarios respecto a 2015.
