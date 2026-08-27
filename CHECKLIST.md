# Checklist de entrega — Actividad 1 (Streamlit + Docker + Killercoda)

Marcar en orden. Los bloques A y B ya están hechos; empieza en el C.

---

## A. Proyecto local — ✅ HECHO

- [x] Dataset generado (`data/ventas_retail.csv`, 12.000 filas)
- [x] `app.py` con filtros, KPIs y 5 pestañas de análisis
- [x] `requirements.txt` con versiones fijadas
- [x] `Dockerfile`, `.dockerignore`, `docker-compose.yml`
- [x] `.streamlit/config.toml` (CORS/XSRF desactivados — necesario para Killercoda)
- [x] `README.md` con documentación

## B. Verificación local — ✅ HECHO

- [x] La app levanta sin errores
- [x] Las 5 pestañas renderizan sin excepciones

---

## C. Revisar la app con tus propios ojos (5 min)

- [ ] Levantar la app:
      `streamlit run app.py`
- [ ] Abrir <http://localhost:8501>
- [ ] Mover el rango de fechas y confirmar que los KPIs cambian
- [ ] Entrar a cada pestaña: Evolución, Productos, Territorio, Clientes, Datos
- [ ] Probar el botón de descarga CSV en la pestaña *Datos*
- [ ] Decidir si cambias algo (colores, títulos, alguna métrica). Si sí, pídemelo ahora.

## D. Subir el código a GitHub (recomendado — simplifica mucho el paso F)

- [ ] Crear repositorio público en GitHub, ej. `dashboard-ventas-streamlit`
- [ ] Desde la carpeta del proyecto:
      `git init`
      `git add .`
      `git commit -m "Dashboard de ventas con Streamlit y Docker"`
      `git branch -M main`
      `git remote add origin https://github.com/USUARIO/dashboard-ventas-streamlit.git`
      `git push -u origin main`
- [ ] Confirmar en GitHub que subió `data/ventas_retail.csv` (1.6 MB, entra sin problema)

> Si no quieres usar GitHub, sáltate este bloque y en el paso F usa *Upload File*.

## E. Abrir Killercoda

- [ ] Entrar a <https://killercoda.com> e iniciar sesión (GitHub sirve)
- [ ] Abrir el playground **Ubuntu** o **Docker**
- [ ] Verificar Docker: `docker --version`

## F. Llevar el proyecto al playground

**Opción 1 — con GitHub (rápida):**
- [ ] `git clone https://github.com/USUARIO/dashboard-ventas-streamlit.git`
- [ ] `cd dashboard-ventas-streamlit`
- [ ] `ls -la` para confirmar que están `app.py`, `Dockerfile`, `data/` y `.streamlit/`

**Opción 2 — subida manual:**
- [ ] `mkdir -p ~/dashboard/data ~/dashboard/.streamlit && cd ~/dashboard`
- [ ] Menú ☰ → *Upload File* para cada archivo
- [ ] Mover cada archivo a su carpeta correcta (`data/`, `.streamlit/`)
- [ ] ⚠️ Verificar que `.streamlit/config.toml` existe — es un archivo oculto y es el que más se olvida

## G. Construir y ejecutar el contenedor

- [ ] `docker build -t dashboard-ventas:1.0 .`
      (la primera vez tarda unos minutos; debe terminar en *naming to docker.io/library/dashboard-ventas:1.0*)
- [ ] `docker images` → aparece `dashboard-ventas`
- [ ] `docker run -d --name dashboard-ventas -p 8501:8501 dashboard-ventas:1.0`
- [ ] `docker ps` → estado `Up` (a los ~30 s pasa a `healthy`)
- [ ] `curl -s http://localhost:8501/_stcore/health` → responde `ok`
- [ ] Si algo falla: `docker logs dashboard-ventas`

## H. Exponer el puerto y abrir el dashboard

- [ ] Barra superior de Killercoda → **Traffic / Ports** → *Custom Ports*
- [ ] Escribir `8501` → *Access*
- [ ] Se abre una URL tipo `https://<id>-8501-<host>.killercoda.com`
- [ ] Confirmar que el dashboard carga (si queda en "Connecting…", revisar `.streamlit/config.toml`)
- [ ] Probar un filtro en la URL pública para demostrar que es interactivo

## I. Capturar la evidencia

- [ ] `mkdir capturas` en tu PC
- [ ] Captura 1: terminal con `docker images` y `docker ps` (imagen + contenedor healthy)
- [ ] Captura 2: build completado (`Successfully tagged` / `naming to ...`)
- [ ] Captura 3: dashboard abierto en la URL pública, con la URL de Killercoda visible en la barra
- [ ] Captura 4: dashboard con filtros aplicados (ej. Tecnología + Norte) mostrando KPIs distintos
- [ ] Captura 5: una pestaña de análisis potente (Pareto o Territorio)
- [ ] Opcional: grabar un video corto navegando el dashboard

## J. Empaquetar la entrega

- [ ] Carpeta o ZIP con: `app.py`, `data/`, `requirements.txt`, `Dockerfile`, `.dockerignore`, `docker-compose.yml`, `.streamlit/`, `README.md`, `capturas/`
- [ ] Incluir el enlace al repositorio de GitHub (si lo hiciste)
- [ ] Releer el README y reemplazar `USUARIO` por tu usuario real de GitHub
- [ ] Subir a la plataforma del curso

---

## Antes de cerrar el playground

⚠️ Killercoda **borra todo** al expirar la sesión (aprox. 1 hora). Asegúrate de tener las capturas descargadas antes de cerrar la pestaña.
