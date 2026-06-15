"""
Cliente para la API CSV → Parquet.

Dependencias:
    pip install requests

Uso:
    from client import convertir_csv

    resultado = convertir_csv(
        file_path="D:/bases/ribs_2024.csv",
        schema_overrides={"ID": "Int64", "MONTO": "Float64", "ESTADO": "String"},
    )
"""

import requests

# Cambia esta URL si el servidor está en otra dirección o puerto
API_BASE_URL =  "http://localhost:8000"


def convertir_csv(
    file_path: str,
    schema_overrides: dict[str, str] | None = None,
    columns: list[str] | None = None,
    separator: str = ",",
    null_values: str = ",NULL,null,NA,N/A,na,n/a",
    timeout: int = 3600,
) -> dict:
    """
    Llama al endpoint POST /convert de la API.

    Parámetros
    ----------
    file_path       : Ruta absoluta al CSV **en el servidor**.
    schema_overrides: {nombre_columna: tipo_polars}.
                      Si se omite `columns`, las columnas se infieren de aquí.
                      Tipos válidos: Int8/16/32/64, UInt8/16/32/64,
                                     Float32/64, String, Boolean, Date, Datetime.
    columns         : Lista explícita de columnas a cargar.
                      Opcional si se pasa schema_overrides.
    separator       : Separador del CSV (default: coma).
    null_values     : Valores tratados como nulos, separados por coma.
    timeout         : Segundos máximos de espera (default: 1 hora).

    Retorna
    -------
    Diccionario con la respuesta de la API:
        {
            "status":          "success",
            "input_file":      "...",
            "output_file":     "...",
            "rows":            4500000,
            "columns_loaded":  [...],
            "chunks_processed": 15,
            "workers_used":    7,
            "elapsed_seconds": 42.3,
            "output_size_mb":  185.4,
        }

    Lanza
    -----
    requests.HTTPError  : Si la API devuelve un código de error (4xx / 5xx).
    requests.Timeout    : Si el servidor no responde antes de `timeout` segundos.
    """
    payload = {"file_path": file_path}

    if schema_overrides:
        payload["schema_overrides"] = schema_overrides

    if columns:
        payload["columns"] = columns

    response = requests.post(
        f"{API_BASE_URL}/convert",
        json=payload,
        params={"separator": separator, "null_values": null_values},
        timeout=timeout,
    )

    if not response.ok:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise requests.HTTPError(
            f"{response.status_code} {response.reason} — Detalle: {detail}",
            response=response,
        )

    return response.json()


# ---------------------------------------------------------------------------
# Ejemplo de uso directo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    resultado = convertir_csv(
        file_path="D:/bases/ribs_2024.csv",
        schema_overrides={
            "ID_CLIENTE": "Int64",
            "NOMBRE":     "String",
            "MONTO":      "Float64",
            "FECHA":      "String",
            "ESTADO":     "String",
        },
        separator=",",
    )

    print(f"Archivo generado : {resultado['output_file']}")
    print(f"Filas procesadas : {resultado['rows']:,}")
    print(f"Columnas cargadas: {resultado['columns_loaded']}")
    print(f"Tiempo total     : {resultado['elapsed_seconds']} seg")
    print(f"Tamaño parquet   : {resultado['output_size_mb']} MB")
