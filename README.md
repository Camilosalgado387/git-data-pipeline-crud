# 🚀 Data Pipeline & Dataset Catalog API
> Un proyecto práctico en Python diseñado para **dominar Git, GitHub y CI/CD** en tu transición hacia **Data Engineering**.

---

## 🎯 Objetivo del Proyecto

Como analista de datos que busca escalar a **Data Engineer**, tu objetivo es adoptar las prácticas de ingeniería de software que garantizan que el código y los pipelines sean **reproducibles, confiables y automatizados**.

Este proyecto es una API REST construida con **FastAPI** y **SQLite** que emula un catálogo de metadatos de pipelines de datos (datasets, esquemas, fuentes y ejecuciones de ingesta), estructurada para acompañarte paso a paso en **6 Misiones Prácticas de Git y GitHub**.

---

## 📂 Estructura del Repositorio

```text
git-data-pipeline-crud/
├── .github/
│   └── workflows/
│       └── ci.yml               # Pipeline de CI (Linting + Tests en cada PR)
├── app/
│   ├── __init__.py
│   ├── database.py              # Capa de persistencia SQLite y lógica CRUD
│   ├── main.py                  # Endpoints de FastAPI y documentación OpenAPI
│   └── models.py                # Esquemas y validación con Pydantic
├── tests/
│   ├── __init__.py
│   └── test_main.py             # Pruebas unitarias con Pytest y TestClient
├── .gitignore                   # Higiene de Git: ignora DBs, datos crudos y caches
├── requirements.txt             # Dependencias del proyecto
└── README.md                    # Esta guía y manual de misiones
```

---

## ⚙️ Configuración Rápida en Local

Abre una terminal (`cmd` o `powershell`) en la carpeta del proyecto:

```bash
cd C:\Users\camil\git-data-pipeline-crud
```

### 1. Crear y activar entorno virtual
```bash
python -m venv venv
```
- En Windows PowerShell:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- En Windows CMD:
  ```cmd
  venv\Scripts\activate.bat
  ```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Ejecutar los tests automáticos
```bash
pytest -v tests/
```

### 4. Iniciar el servidor local
```bash
uvicorn app.main:app --reload --port 8000
```
Visita la documentación interactiva (Swagger UI) en tu navegador:
👉 **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 🗺️ Roadmap de Misiones Git & CI/CD

Completa estas misiones en orden para afianzar cada concepto clave:

### 📍 Misión 1: Inicialización limpia e higiene de Git
- **Concepto clave:** `.gitignore` y Commits Convencionales.
- **Acción:**
  1. Inicializa el repositorio local:
     ```bash
     git init
     ```
  2. Revisa el estado de los archivos:
     ```bash
     git status
     ```
     *(Verifica que archivos de base de datos `.db` o la carpeta `venv/` NO aparezcan en los archivos sin seguimiento).*
  3. Agrega los archivos al área de preparación (staging):
     ```bash
     git add .
     ```
  4. Crea tu primer commit semántico:
     ```bash
     git commit -m "feat: initial project setup with dataset catalog API and tests"
     ```

---

### 📍 Misión 2: Feature Branching y desarrollo atómico
- **Concepto clave:** Nunca desarrollar directamente sobre `main`. Ramas de funcionalidad aisladas.
- **Acción:**
  1. Crea una nueva rama para una funcionalidad:
     ```bash
     git switch -c feature/add-dataset-metrics
     # o clásicamente: git checkout -b feature/add-dataset-metrics
     ```
  2. Realiza un pequeño cambio (ej. añadir un campo nuevo en `app/models.py` o un nuevo endpoint).
  3. Comprueba las diferencias exactas:
     ```bash
     git diff
     ```
  4. Haz commits pequeños y claros:
     ```bash
     git add app/models.py
     git commit -m "feat(models): add quality_score field to dataset response"
     ```
  5. Regresa a `main` y observa cómo el código vuelve a su estado original:
     ```bash
     git switch main
     ```

---

### 📍 Misión 3: GitHub Remoto y Pull Requests (PR)
- **Concepto clave:** Colaboración remota, revisión de código (*Code Review*).
- **Acción:**
  1. Entra a [GitHub.com](https://github.com) y crea un nuevo repositorio vacío llamado `git-data-pipeline-crud`.
  2. Conecta tu repositorio local con GitHub:
     ```bash
     git branch -M main
     git remote add origin https://github.com/TU_USUARIO/git-data-pipeline-crud.git
     git push -u origin main
     ```
  3. Sube tu rama de funcionalidad:
     ```bash
     git push -u origin feature/add-dataset-metrics
     ```
  4. En GitHub, verás un botón **Compare & pull request**. Haz clic y abre un Pull Request hacia `main`. Escribe una descripción detallada explicando qué problema resuelve tu cambio.

---

### 📍 Misión 4: CI/CD en Acción con GitHub Actions
- **Concepto clave:** Integración continua que valida calidad antes de mezclar código a producción.
- **Acción:**
  1. Al abrir el Pull Request en GitHub, observa la pestaña de **Checks**. Verás cómo GitHub lanza una máquina virtual con Ubuntu que:
     - Instala las dependencias.
     - Ejecuta `ruff check .` (linter).
     - Ejecuta `pytest` (pruebas automáticas).
  2. **Experimento de aprendizaje:** En tu rama local, introduce intencionalmente un error de sintaxis o rompe una prueba en `tests/test_main.py`.
  3. Haz commit y `git push`.
  4. Observa cómo GitHub Actions detecta el error y bloquea el merge en rojo ❌.
  5. Corrige el error en local, haz push y observa cómo se vuelve verde ✅.

---

### 📍 Misión 5: Simulación y Resolución de Conflictos (Merge Conflicts)
- **Concepto clave:** Perder el miedo a los conflictos entre ramas y resolverlos con confianza.
- **Acción:**
  1. En la rama `main`, edita la versión en `app/main.py` a `"0.2.0"`, haz commit y push:
     ```bash
     git switch main
     # Modifica version="0.2.0" en app/main.py
     git commit -am "chore: bump version to 0.2.0"
     ```
  2. En otra rama (`feature/quick-fix`), modifica la misma línea a `"0.1.1"`:
     ```bash
     git switch -c feature/quick-fix
     # Modifica version="0.1.1" en app/main.py
     git commit -am "fix: patch version to 0.1.1"
     ```
  3. Intenta mezclar `main` en tu rama:
     ```bash
     git merge main
     ```
  4. Git te avisará de un conflicto: `CONFLICT (content): Merge conflict in app/main.py`.
  5. Abre `app/main.py` en tu editor. Verás los marcadores:
     ```python
     <<<<<<< HEAD
     version="0.1.1",
     =======
     version="0.2.0",
     >>>>>>> main
     ```
  6. Decide cuál versión mantener, borra los marcadores, guarda el archivo y concluye el merge:
     ```bash
     git add app/main.py
     git commit -m "merge: resolve version conflict with main"
     ```

---

### 📍 Misión 6: Releases y Semantic Versioning (Git Tags)
- **Concepto clave:** Etiquetado de versiones estables de producción (`v0.1.0`, `v1.0.0`).
- **Acción:**
  1. Estando en `main` con todos los cambios integrados:
     ```bash
     git switch main
     git pull origin main
     ```
  2. Crea un tag anotado:
     ```bash
     git tag -a v0.1.0 -m "Release v0.1.0: First stable dataset catalog API"
     ```
  3. Sube el tag a GitHub:
     ```bash
     git push origin v0.1.0
     # o todos los tags: git push origin --tags
     ```
  4. En GitHub, ve a la sección **Releases** para ver tu primer release publicado.

---

## 📈 Próximos pasos hacia Data Engineering

Una vez completadas las 6 misiones de Git y CI/CD:
1. **Contenedorización (Docker):** Crear un `Dockerfile` y un `docker-compose.yml` para levantar la API junto con un PostgreSQL real.
2. **Validación de Datos:** Integrar `pydantic` o `great_expectations` para validar schemas de datasets entrantes.
3. **Orquestación:** Configurar una tarea en Prefect o Dagster que consuma esta API para registrar ejecuciones de ingesta reales.
