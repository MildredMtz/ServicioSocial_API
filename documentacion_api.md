# Documentación API — CSV a Parquet Converter

---

## 2. Descripción General de la Solución

Esta API permite transformar archivos CSV de gran tamaño al formato Parquet, un formato de almacenamiento columnar optimizado para análisis de datos. Fue diseñada para manejar bases de datos pesadas de forma eficiente, sin requerir que el archivo quepa completo en memoria.

### Funcionalidades principales

- **Conversión de CSV a Parquet:** recibe la ruta de un archivo CSV y genera automáticamente un archivo `.parquet` en la misma ubicación.
- **Soporte para archivos grandes:** procesa los datos en bloques (chunks) para no saturar la memoria RAM, independientemente del tamaño del archivo.
- **Procesamiento paralelo:** distribuye el trabajo entre múltiples núcleos del servidor para acelerar la conversión.
- **Control de columnas y tipos de datos:** permite indicar qué columnas cargar y qué tipo de dato debe tener cada una (entero, texto, decimal, fecha, etc.).
- **Manejo de valores nulos:** reconoce automáticamente representaciones comunes de datos vacíos (`NULL`, `NA`, `N/A`, etc.).

### Casos de uso

- Convertir bases de datos exportadas desde sistemas legados (en formato CSV con codificación ISO-8859-1) a un formato moderno y eficiente.
- Preparar archivos para su carga en plataformas de análisis como Power BI, Spark, DuckDB o DataBricks.
- Automatizar la transformación de bases periódicas (mensuales, diarias) como parte de un flujo de carga de datos (ETL).

### Beneficios

- **Velocidad:** el procesamiento paralelo reduce significativamente el tiempo de conversión en archivos de millones de filas.
- **Eficiencia en almacenamiento:** el formato Parquet con compresión Snappy ocupa considerablemente menos espacio que el CSV original.
- **Compatibilidad:** el archivo resultante puede ser consumido directamente por las principales herramientas de análisis y bases de datos modernas.
- **Simplicidad de uso:** basta con indicar la ruta del archivo y, opcionalmente, las columnas de interés; la API se encarga del resto.

---

## 3. Arquitectura General

> Diagrama interactivo: [ver en Excalidraw](https://excalidraw.com/#json=arP4ehy3dY-halJPDi_N1,5F6BAKXjjPSt7Kxwrp40ew)  

### Vista de alto nivel

La solución sigue un flujo lineal de tres zonas: **Origen → API (servidor) → Destino**. El cliente envía una solicitud HTTP indicando qué archivo convertir; la API procesa el archivo internamente y deposita el resultado en disco, listo para ser consumido.

### Componentes involucrados

| Componente | Rol |
|---|---|
| **Cliente / Script** | Quien dispara la conversión mediante una llamada HTTP POST |
| **FastAPI** | Punto de entrada de la API; recibe y valida las solicitudes |
| **ThreadPool** | Puente que permite ejecutar operaciones de archivo sin bloquear la API |
| **Chunker** | Lee el CSV original en bloques para no saturar la memoria |
| **ProcessPoolExecutor** | Distribuye los bloques entre varios núcleos de CPU en paralelo |
| **Polars** | Motor de parseo: convierte cada bloque CSV en formato Parquet en memoria |
| **ParquetWriter** | Ensambla todos los bloques procesados y escribe el archivo final en disco |

### Sistemas origen y destino

- **Origen:** archivo CSV con codificación ISO-8859-1, ubicado en el sistema de archivos del servidor. El cliente solo necesita indicar su ruta.
- **Destino:** archivo `.parquet` generado en la misma carpeta que el CSV original, comprimido con Snappy. Puede ser consumido directamente por herramientas como Power BI, Spark, DuckDB o DataBricks.

### Flujo de información

1. El cliente envía una solicitud `POST /convert` con la ruta del archivo y parámetros opcionales.
2. FastAPI recibe la solicitud y la delega al motor de conversión a través de un ThreadPool.
3. El Chunker abre el CSV y lo divide en bloques de N líneas (configurable).
4. Cada bloque se envía a un proceso hijo que usa Polars para parsearlo y devolverlo como bytes Parquet.
5. El ParquetWriter recibe todos los bloques en orden y los escribe como un único archivo `.parquet`.
6. La API devuelve al cliente un resumen: filas procesadas, tamaño del archivo, tiempo transcurrido.

### Dependencias externas

| Librería | Función |
|---|---|
| **FastAPI + Uvicorn** | Servidor HTTP y framework de la API |
| **Polars** | Parseo de CSV y conversión a Parquet en memoria |
| **PyArrow** | Escritura final del archivo Parquet en disco |
| **Python multiprocessing / concurrent.futures** | Paralelización del procesamiento por núcleos de CPU |
