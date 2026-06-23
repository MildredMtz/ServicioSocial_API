# Servicio Social - API 
En este repositorio se adjuntan los cambios realizados para convertir archivos CSV a formato Parquet mediante una API desarrollada en Python y una interfaz gráfica web que facilita el procesamiento de múltiples archivos.

## Fronted 
Se desarrolló una interfaz gráfica para que el proceso de conversión sea más intuitivo y eficiente para los usuarios.

## Archivo por archivo
Permite ingresar rutas de acceso individuales a archivos CSV para convertirlos a formato Parquet.

### Botones y apartados
- Servidor API: El campo de texto con http://localhost:8000 es la dirección donde está corriendo la API. 
- Botón "Verificar conexión": le pregunta a la API si está activa. Si responde, el punto se pone verde. 
**NOTA** Úsalo siempre primero antes de intentar convertir para confirmar que uvicorn sigue corriendo en la terminal.
- Archivos a convertir: La caja grande con placeholder D:/bases/mi_archivo.csv es donde se escribe la ruta del CSV.
- Separador & nulos:
  - Sep → el carácter que divide las columnas en tu CSV. El default es ,. Si abres tu archivo y ves que las columnas están separadas por ;, cambia esto a ;. 
  - Nulos → lista de valores que la API debe interpretar como "celda vacía". El default ya cubre los más comunes: ,NULL,null,NA,N/A,na,n/a.
- Tipo de dato por columna: Aquí le dices a la API qué tipo de dato tiene cada columna. Es opcional porque Polars puede inferirlo solo, en caso de ponerlo lo refuerzas colocando el tipo de dato que tú quieres.
- Botón "+ columna / tipo": Agrega una fila extra para definir el tipo de dato. Esta cuenta con dos aparatados
  - La de la izquierda → nombre exacto de la columna tal como aparece en el CSV (con mayúsculas, espacios y acentos).
  - La de la derecha → tipo de dato en formato Polars. Los tipos válidos son: Int8, Int16, Int32, Int64, Float32, Float64, String, Boolean, Date, Datetime
- Botón "+ Agregar archivo": Añade una nueva tarjeta para un segundo CSV. Cada tarjeta es independiente — puede tener su propia ruta, separador y schema. Los convierte todos al mismo tiempo cuando presionas "Convertir todos".
- Botón "Convertir todos": Arranca la conversión de todos los archivos en paralelo. Mientras procesa verás la barra morada avanzando. Al terminar cada tarjeta muestra chips verdes con el resumen: filas, MB, segundos, chunks usados y el nombre del .parquet generado.

## Explorador de carpeta
Permite navegar entre carpetas del sistema para localizar archivos CSV disponibles para su conversión.

### Botones y apartados
- Ruta de carpeta: Campo donde se especifica la carpeta que se desea explorar.
- Botón "Explorar": Consulta la API y muestra las carpetas y archivos CSV contenidos en la ruta indicada.
- Subcarpetas: Lista de carpetas encontradas dentro de la ruta actual.
- Archivos CSV encontrados: Lista de archivos CSV detectados en la carpeta explorada.
- Indicador Parquet: Muestra si el archivo CSV ya cuenta con una versión Parquet generada.

### Funcionamiento

El explorador únicamente muestra:
- Archivos CSV ubicados en la carpeta seleccionada.
- Subcarpetas inmediatas de dicha carpeta.

## Búsqueda recursiva

Permite localizar automáticamente todos los archivos CSV contenidos dentro de una carpeta y todas sus subcarpetas, sin necesidad de navegar manualmente por cada directorio.

### Botones y apartados
- Ruta raíz: Carpeta principal desde donde comenzará la búsqueda.
- Botón "Buscar CSV": Realiza una exploración recursiva de todas las carpetas internas.
- Resultados encontrados: Lista completa de archivos CSV localizados.
- Contador de carpetas exploradas: Indica cuántas carpetas fueron revisadas durante la búsqueda.

## Pasos de ejecución
1. Abrir la página donde tenemos nuestra interfáz gráfica, en este caso hacemos doble click en  csv_converter_ui.html, este nos va a redirigir a una ventana en nuestro navegador. 

2. Abrir una terminal en la ruta donde se encuentra el archivo api.py y client.py, una vez dentro activamos nuestro puerto verificando que sea el mismo que se encuentra en client.py y en el fronted en el apartado "Servidor API" 

   ```bash
   python -m uvicorn api:app --host 0.0.0.0 --port 8000 --workers 1

Si nuestro puerto se activa de forma correcta tendremos una salida en terminal similar a esta 
    ```bash
    INFO:     Started server process [7724]
    INFO:     Waiting for application startup.
    INFO:     Application startup complete.
    INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)

3. Nos dirigimos a la página del navegador que abrimos y en ""Servidor API" pulsamos el botón "Verificar conexión", si la conexión es correcta se pondrá el puntito en color verde.
En caso de que se ponga en color rojo verificar que los puertos sean los mismos.

4. Una vez establecida la conexión con la API, el sistema ofrece tres formas distintas de trabajar con los archivos CSV.

### Opción 1: Archivo por archivo: 
#### Pasos
- Ir a la pestaña Archivo por archivo.
- En el apartado Archivos a convertir, ingresar la ruta completa del archivo CSV.
##### Ejemplo:
D:\Bases\pacientes.csv
   
- Si se desea convertir más de un archivo, presionar + Agregar archivo.
- Presionar Convertir todos.
- Esperar a que finalice el procesamiento y revisar el resumen generado.

#### Cuándo utilizar esta opción
- Cuando se conocen las rutas exactas de los archivos.
- Cuando se desea configurar un esquema de tipos de datos específico.
- Cuando se van a convertir pocos archivos.

### Opción 2: Explorador de carpetas

#### Pasos
- Ir a la pestaña Explorador de carpetas.
- Ingresar la ruta de la carpeta que se desea revisar.

##### Ejemplo:
D:\Datos

- Presionar Explorar.
- El sistema mostrará:
  - Los archivos CSV encontrados en esa carpeta.
  - Las subcarpetas disponibles.
  - Una vez localizado el archivo CSV deseado, proceder con la conversión.

#### Cuándo utilizar esta opción
- Cuando no se conoce exactamente la ubicación del archivo.
- Cuando se desea navegar manualmente por la estructura de carpetas.
- Cuando se trabaja con directorios pequeños o medianos.

### Opción 3: Búsqueda recursiva

#### Pasos
- Ir a la pestaña Búsqueda recursiva.
- Ingresar la carpeta raíz desde donde comenzará la búsqueda.

##### Ejemplo:
D:\Datos

- Presionar Buscar CSV.
- El sistema recorrerá todas las subcarpetas de forma automática.Se mostrará una lista con todos los archivos CSV encontrados y sus rutas completas.
- Seleccionar los archivos que se desean convertir y ejecutar la conversión.

#### Cuándo utilizar esta opción
- Cuando existen muchas subcarpetas.
- Cuando no se conoce la ubicación exacta de los archivos CSV.
- Cuando se desea localizar rápidamente todos los CSV de un proyecto o repositorio de datos.


