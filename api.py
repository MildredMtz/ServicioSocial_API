"""
API REST para convertir archivos CSV (ISO-8859-1) a Parquet usando Polars.

Dependencias:
    pip install fastapi uvicorn[standard] polars pyarrow

Ejecutar:
    python -m uvicorn api:app --host 0.0.0.0 --port 8000 --workers 1
"""

from __future__ import annotations

import io
import logging
import multiprocessing
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import polars as pl
import pyarrow.parquet as pq
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Líneas por chunk: ajustar según RAM disponible y tamaño de fila promedio.
CHUNK_LINES: int = int(os.getenv("CHUNK_LINES", 300_000))

# Procesos paralelos para parsear chunks. Deja 1 núcleo libre para el SO.
MAX_WORKERS: int = max(1, int(os.getenv("MAX_WORKERS", multiprocessing.cpu_count() - 1)))

# ---------------------------------------------------------------------------
# Mapa de tipos Polars (recibe strings desde JSON)
# ---------------------------------------------------------------------------

_POLARS_TYPE_MAP: dict[str, pl.PolarsDataType] = {
    "Int8": pl.Int8,
    "Int16": pl.Int16,
    "Int32": pl.Int32,
    "Int64": pl.Int64,
    "UInt8": pl.UInt8,
    "UInt16": pl.UInt16,
    "UInt32": pl.UInt32,
    "UInt64": pl.UInt64,
    "Float32": pl.Float32,
    "Float64": pl.Float64,
    "String": pl.String,
    "Utf8": pl.String,
    "Boolean": pl.Boolean,
    "Date": pl.Date,
    "Datetime": pl.Datetime,
}


def _resolve_dtype(name: str) -> pl.PolarsDataType:
    dtype = _POLARS_TYPE_MAP.get(name)
    if dtype is None:
        raise ValueError(
            f"Tipo Polars desconocido: '{name}'. "
            f"Tipos válidos: {list(_POLARS_TYPE_MAP)}"
        )
    return dtype


# ---------------------------------------------------------------------------
# Modelos de request / response
# ---------------------------------------------------------------------------


class ConvertRequest(BaseModel):
    """
    Parámetros del endpoint POST /convert.

    - file_path       : Ruta absoluta al archivo CSV.
    - columns         : Lista de columnas a cargar. Si se omite se infiere
                        de las keys de schema_overrides.
    - schema_overrides: Diccionario {nombre_columna: tipo_polars_str}.
                        Ejemplo: {"ID": "Int64", "NOMBRE": "String"}.
    """

    file_path: str
    columns: list[str] | None = None
    schema_overrides: dict[str, str] | None = None

class ConvertResponse(BaseModel):
    status: str
    input_file: str
    output_file: str
    rows: int
    columns_loaded: list[str]
    chunks_processed: int
    workers_used: int
    elapsed_seconds: float
    output_size_mb: float


# ---------------------------------------------------------------------------
# Worker de multiprocessing (debe estar en nivel de módulo para pickle)
# ---------------------------------------------------------------------------


def _chunk_worker(
    chunk_bytes: bytes,
    columns: list[str] | None,
    schema_str: dict[str, str] | None,
    separator: str,
    null_values: list[str],
) -> bytes:
    """
    Parsea un chunk CSV (UTF-8) con Polars y devuelve bytes Parquet.
    Se ejecuta en un proceso hijo; devuelve bytes para evitar problemas
    de serialización de DataFrames entre procesos.
    """
    schema_overrides: dict[str, pl.PolarsDataType] | None = None
    if schema_str:
        schema_overrides = {
            col: _POLARS_TYPE_MAP.get(dtype_name, pl.String)
            for col, dtype_name in schema_str.items()
        }

    df = pl.read_csv(
        io.BytesIO(chunk_bytes),
        columns=columns if columns else None,
        schema_overrides=schema_overrides,
        separator=separator,
        null_values=null_values,
        infer_schema_length=0 if schema_overrides else 1_000,
        truncate_ragged_lines=True,
        ignore_errors=True,
        encoding="utf8",
    )
    buf = io.BytesIO()
    df.write_parquet(buf, compression="snappy")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Lógica principal de conversión (síncrona, se ejecuta en threadpool)
# ---------------------------------------------------------------------------


def _convert(
    file_path: str,
    columns: list[str] | None,
    schema_overrides: dict[str, str] | None,
    separator: str,
    null_values: list[str],
) -> ConvertResponse:
    t0 = time.perf_counter()

    # --- Validaciones previas ---
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

    output_path = str(Path(file_path).with_suffix(".parquet"))

    # Si solo se pasa schema_overrides, inferir columnas desde sus keys
    if not columns and schema_overrides:
        columns = list(schema_overrides.keys())

    # Resolver tipos Polars (falla rápido si alguno es inválido)
    if schema_overrides:
        for col, dtype_str in schema_overrides.items():
            _resolve_dtype(dtype_str)  # lanza ValueError si no existe

    logger.info(
        "Iniciando conversión: %s | columnas=%s | workers=%d | chunk_lines=%d",
        file_path,
        columns or "todas",
        MAX_WORKERS,
        CHUNK_LINES,
    )

    # --- Leer el archivo en chunks y re-codificar a UTF-8 ---
    chunks: list[bytes] = []

    with open(file_path, "r", encoding="iso-8859-1", errors="replace") as fh:
        header_line = fh.readline()  # primera línea = encabezado

        buffer: list[str] = []
        for raw_line in fh:
            buffer.append(raw_line)
            if len(buffer) >= CHUNK_LINES:
                text = header_line + "".join(buffer)
                chunks.append(text.encode("utf-8", errors="replace"))
                buffer.clear()

        if buffer:  # último chunk (puede ser < CHUNK_LINES)
            text = header_line + "".join(buffer)
            chunks.append(text.encode("utf-8", errors="replace"))

    total_chunks = len(chunks)
    logger.info("Chunks generados: %d", total_chunks)

    if total_chunks == 0:
        raise ValueError("El archivo CSV está vacío o solo contiene encabezado.")

    # --- Procesar chunks en paralelo ---
    worker_args = [
        (chunk, columns, schema_overrides, separator, null_values)
        for chunk in chunks
    ]

    parquet_pieces: dict[int, bytes] = {}

    if total_chunks == 1 or MAX_WORKERS == 1:
        # Modo single-process: sin overhead de IPC
        for i, args in enumerate(worker_args):
            parquet_pieces[i] = _chunk_worker(*args)
            logger.info("Chunk %d/%d procesado.", i + 1, total_chunks)
    else:
        with ProcessPoolExecutor(max_workers=MAX_WORKERS) as pool:
            future_to_idx = {
                pool.submit(_chunk_worker, *args): i
                for i, args in enumerate(worker_args)
            }
            done = 0
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                parquet_pieces[idx] = future.result()
                done += 1
                logger.info("Chunk %d/%d procesado.", done, total_chunks)

    # --- Escribir Parquet incremental (eficiente en RAM) ---
    logger.info("Escribiendo Parquet en: %s", output_path)
    writer: pq.ParquetWriter | None = None
    total_rows = 0

    try:
        for i in range(total_chunks):
            arrow_table = pl.read_parquet(io.BytesIO(parquet_pieces[i])).to_arrow()
            total_rows += len(arrow_table)
            if writer is None:
                writer = pq.ParquetWriter(
                    output_path,
                    arrow_table.schema,
                    compression="snappy",
                )
            writer.write_table(arrow_table)
    finally:
        if writer:
            writer.close()

    elapsed = round(time.perf_counter() - t0, 2)
    out_mb = round(os.path.getsize(output_path) / 1_048_576, 2)

    # Obtener columnas reales del parquet generado
    pq_meta = pq.read_schema(output_path)
    cols_written = list(pq_meta.names)

    logger.info(
        "Conversión completada: %d filas | %.2f MB | %.2fs",
        total_rows,
        out_mb,
        elapsed,
    )

    return ConvertResponse(
        status="success",
        input_file=file_path,
        output_file=output_path,
        rows=total_rows,
        columns_loaded=cols_written,
        chunks_processed=total_chunks,
        workers_used=min(MAX_WORKERS, total_chunks),
        elapsed_seconds=elapsed,
        output_size_mb=out_mb,
    )


# ---------------------------------------------------------------------------
# App FastAPI
# ---------------------------------------------------------------------------

app = FastAPI(
    title="CSV → Parquet Converter",
    description="Convierte archivos CSV grandes (ISO-8859-1) a Parquet usando Polars.",
    version="1.0.0",
)


@app.get("/health", tags=["utilidades"])
def health() -> dict[str, str]:
    """Verifica que el servidor está en línea."""
    return {"status": "ok", "polars_version": pl.__version__}


@app.post("/convert", response_model=ConvertResponse, tags=["conversión"])
async def convert_csv(
    request: ConvertRequest,
    separator: str = ",",
    null_values: str = ",NULL,null,NA,N/A,na,n/a",
) -> ConvertResponse:
    """
    Convierte un CSV a Parquet.

    **Query params opcionales:**
    - `separator`   : Separador de columnas (defecto: `,`).
    - `null_values` : Valores a interpretar como nulos, separados por coma
                      (defecto: ``,NULL,null,NA,N/A,na,n/a`).

    **Body JSON:**
    ```json
    {
      "file_path": "C:/datos/mi_base.csv",
      "columns": ["ID", "NOMBRE", "MONTO"],
      "schema_overrides": {
        "ID":     "Int64",
        "NOMBRE": "String",
        "MONTO":  "Float64"
      }
    }
    ```
    Si se omite `columns`, se infiere de las keys de `schema_overrides`.
    """
    null_list = [v for v in null_values.split(",")]

    try:
        result = await run_in_threadpool(
            _convert,
            request.file_path,
            request.columns,
            request.schema_overrides,
            separator,
            null_list,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error inesperado durante la conversión.")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return result
