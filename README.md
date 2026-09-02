
# Microservicio encargado de procesar y exponer los endpoints de inteligencia de negocios y agregación de datos para alimentar el Dashboard principal de la aplicación.

---

## 🛠️ Tecnologías Utilizadas

* **Lenguaje:** Python 3.11+
* **Framework:** Flask
* **ORM / Conectores:** SQLAlchemy / Psycopg2
* **Base de Datos:** PostgreSQL (Modo Lectura)
* **Contenedorización:** Docker / Docker Compose

---

## 💡 Funcionalidades Principales

* **RF-04 Dashboard & Agregación:** Consultas SQL de agregación (`GROUP BY tipo_factura`, `SUM(total)`) expuestas en APIs RESTful[cite: 1].
* **Consumo de BD Compartida:** Acceso directo a la base de datos PostgreSQL de facturación en modo lectura para maximizar la velocidad de cálculo de métricas.

---

## 🚀 Instalación y Ejecución Local

### Prerrequisitos
* Python 3.11+.
* Docker Desktop y la red externa `global-invoice-net` activa (`docker network create global-invoice-net`).

### 1. Variables de Entorno (`.env`)
Crea un archivo `.env` en la raíz del proyecto:
```env
PORT=5000
DB_HOST=postgres-db
DB_PORT=5432
DB_NAME=global_invoice
DB_USER=postgres
DB_PASSWORD=postgres_password
DATABASE_URL=postgresql://postgres:postgres_password@postgres-db:5432/global_invoice


### Ejecutar con docker

docker compose up --build