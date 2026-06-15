# Servicio Social - API 
En este repositorio se adjuntan cambios que se hicieron a la API para pasar archivos csv a parquet.

## Fronted 
Se realizó un fronted para que este sea más intuitivo para los usuarios y para que sea más eficiente a la hora de pasar múltiples csv. En este caso únicamente se conecta con la API, se selcciona la/las rutas de los csv que se quieren cambian a parquet, se llenan los campos en caso de ser necesario y se selecciona el botón "Convertir todos". 

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

### Pasos 
1. Abrir la página donde tenemos nuestro fronted, en este caso hacemos doble click en el archivo csv_converter_ui.html, este nos va a redirigir a una ventana en nuestro navegador. 

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

4. Una vez que establecimos conexión con nuestra API pasamos al apartado "Archivos a convertir", en la parte superior tenemos "#01 D:/bases/mi_archivo.csv" en este apartado colocamos nuestra ruta de acceso al archivo csv, en caso de querer convertir más de un archivo pulsamos el botón "+ Agregar archivo", este nos abrirá un nuevo apartado y de igual manera colocamos la ruta de acceso.
Una vez que ya tengamos todos los archivos que queremos convertir a parquet seleccionamos "Convertit todos".

5. Finalmente se nos dará un resumen de cuántos archivos se procesaron, filas totales, el tamaño total, nombre del archivo parquet descargado y el tiempo en el que se completó la tarea. 