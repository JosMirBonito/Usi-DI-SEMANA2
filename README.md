# Actividad 1 — Dashboard interactivo con Streamlit y Docker

Dashboard de análisis de ventas retail construido con **Streamlit + Plotly**, contenedorizado con **Docker** y desplegado en **Killercoda**.

---

## 1. Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `app.py` | Aplicación Streamlit (dashboard completo, 5 secciones) |
| `data/ventas_retail.csv` | Dataset: 12.000 transacciones, 18 columnas, 2023–2025 |
| `data/generar_dataset.py` | Script reproducible que genera el dataset (semilla fija = 42) |
| `requirements.txt` | Dependencias con versiones fijadas |
| `Dockerfile` | Imagen de la aplicación |
| `docker-compose.yml` | Despliegue alternativo con Compose |
| `.dockerignore` | Exclusiones del contexto de build |
| `.streamlit/config.toml` | Configuración de servidor y tema |

---

## 2. Dataset

Dataset **sintético** de ventas retail (generado con NumPy, semilla fija para que sea reproducible). Se optó por generarlo para que el contenedor no dependa de descargas externas y para poder inyectar patrones analíticamente interesantes: estacionalidad anual, picos de campaña (julio y noviembre–diciembre), efecto fin de semana, márgenes distintos por categoría y una tasa de devolución más alta en Marketplace.

- **Filas:** 12.000 · **Columnas:** 18 · **Periodo:** 01/01/2023 – 31/12/2025
- **Dimensiones:** ciudad, región, canal, categoría, producto, segmento de cliente, método de pago
- **Métricas:** precio unitario, cantidad, descuento, ingreso, costo, utilidad, satisfacción, días de envío, devuelto

Para regenerarlo:

```bash
python data/generar_dataset.py
```

---

## 3. Funcionalidades del dashboard

**Filtros interactivos (barra lateral):** rango de fechas, categoría, región, canal, segmento de cliente, rango de ticket (slider), interruptor para incluir/excluir devoluciones y selector de granularidad temporal (diaria / semanal / mensual).

**KPIs:** ingresos, utilidad, margen %, ticket promedio y unidades vendidas — cada uno con **variación automática contra el periodo anterior de igual duración**.

**5 pestañas de análisis:**

1. **Evolución** — serie temporal con media móvil, utilidad superpuesta y **proyección lineal por mínimos cuadrados** con horizonte configurable; heatmap de estacionalidad (día de semana × mes); área 100% del mix por canal.
2. **Productos** — Top N configurable, sunburst categoría → producto y **análisis de Pareto 80/20** con eje secundario acumulado.
3. **Territorio** — treemap región/ciudad coloreado por margen, dispersión volumen vs ingresos y tabla comparativa con barras de progreso.
4. **Clientes** — donut por segmento, ingresos por método de pago, satisfacción por canal, dispersión descuento vs utilidad y **matriz de correlación**.
5. **Datos** — buscador de texto, tabla completa y **descarga en CSV** del detalle filtrado y del resumen agregado.

---

## 4. Ejecución local (sin Docker)

```bash
pip install -r requirements.txt
```

```bash
streamlit run app.py
```

Abrir <http://localhost:8501>.

---

## 5. Ejecución con Docker

Construir la imagen:

```bash
docker build -t dashboard-ventas:1.0 .
```

Levantar el contenedor:

```bash
docker run -d --name dashboard-ventas -p 8501:8501 dashboard-ventas:1.0
```

Verificar que está corriendo y sano:

```bash
docker ps
```

Ver logs:

```bash
docker logs -f dashboard-ventas
```

Detener y eliminar:

```bash
docker rm -f dashboard-ventas
```

### Alternativa con Docker Compose

```bash
docker compose up -d --build
```

---

## 6. Despliegue en Killercoda

Entrar a <https://killercoda.com/playgrounds/scenario/ubuntu> (o el playground *Docker*) e iniciar sesión.

**Paso 1 — verificar Docker en el playground:**

```bash
docker --version
```

**Paso 2 — obtener el proyecto.** Si está en GitHub:

```bash
git clone https://github.com/JosMirBonito/Usi-DI-SEMANA2.git && cd Usi-DI-SEMANA2
```

Si no, subir los archivos con el botón **Upload File** del editor de Killercoda (menú ☰ → *Upload File*) y crear la estructura:

```bash
mkdir -p dashboard/data dashboard/.streamlit && cd dashboard
```

**Paso 3 — construir la imagen:**

```bash
docker build -t dashboard-ventas:1.0 .
```

**Paso 4 — ejecutar el contenedor:**

```bash
docker run -d --name dashboard-ventas -p 8501:8501 dashboard-ventas:1.0
```

**Paso 5 — comprobar el estado y el healthcheck:**

```bash
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

```bash
curl -s http://localhost:8501/_stcore/health
```

Debe responder `ok`.

**Paso 6 — abrir el dashboard.** En la barra superior de Killercoda: **Traffic / Ports → Custom Ports**, escribir `8501` y presionar *Access*. Killercoda abre una URL pública del tipo `https://<id>-8501-<host>.killercoda.com`.

> El `Dockerfile` fija `--server.address=0.0.0.0` y `.streamlit/config.toml` desactiva CORS y XSRF, que es lo que permite que el proxy de Killercoda sirva la app sin bloqueos de WebSocket.

**Paso 7 — evidencia.** Capturar pantalla de:
- `docker images` y `docker ps` mostrando la imagen y el contenedor `healthy`
- el dashboard abierto en la URL pública de Killercoda
- al menos una interacción con filtros aplicados (por ejemplo, categoría *Tecnología* + región *Norte*)

Guardar las capturas en una carpeta `capturas/`.

---

## 7. Solución de problemas

| Síntoma | Causa / solución |
|---|---|
| La página carga pero queda "Connecting..." | Falta desactivar CORS/XSRF: verificar que `.streamlit/config.toml` se copió en la imagen. |
| `port is already allocated` | Otro contenedor usa el 8501: `docker rm -f dashboard-ventas` o mapear `-p 8502:8501`. |
| `No se encontro el dataset` | El `COPY data/ ./data/` no encontró el CSV: ejecutar `python data/generar_dataset.py` antes del build. |
| Build lento en Killercoda | Normal la primera vez (descarga de la imagen base y de las dependencias); las reconstrucciones usan caché. |
