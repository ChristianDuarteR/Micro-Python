## Calidad de Código y Métricas (SonarQube via GitHub Actions)

Este microservicio ejecuta automáticamente las pruebas unitarias y el análisis estático de código en cada `push` o `pull_request` a la rama principal a través de **GitHub Actions**.

### Badges de Estado

![CI Workflow](https://github.com/ChristianDuarteR/Micro-Python/actions/workflows/ci.yml/badge.svg)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ChristianDuarteR_Micro-Python&metric=alert_status)](https://sonarcloud.io/summary/overall?id=ChristianDuarteR_Micro-Python)
[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=ChristianDuarteR_Micro-Python&metric=coverage)](https://sonarcloud.io/summary/overall?id=ChristianDuarteR_Micro-Python)
[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=ChristianDuarteR_Micro-Python&metric=bugs)](https://sonarcloud.io/summary/overall?id=ChristianDuarteR_Micro-Python)

### Flujo Automático en CI

El pipeline de GitHub Actions realiza los siguientes pasos de forma automatizada:

1. **Instalación de dependencias:** Configura Python 3.11+ e instala `requirements.txt`.
2. **Ejecución de Pruebas:** Corre `pytest` evaluando los tests y genera el reporte `coverage.xml`.
3. **Verificación de Cobertura:** Comprueba que la cobertura no sea inferior al **80%**.
4. **Análisis de SonarQube:** Envía las métricas (cobertura, bugs, code smells y hotspots de seguridad) a SonarQube / SonarCloud.

*(Nota: Reemplaza `https://sonarqube.example.com` y `global-invoice-metrics` con la URL de tu servidor SonarQube y el Key de tu proyecto).*

### Métricas Analizadas

El reporte de SonarQube evalúa y monitorea los siguientes aspectos:

* **Cobertura de Pruebas (Coverage):** Porcentaje de código ejecutado por `pytest` (Mínimo requerido en CI: **80%**).
* **Bugs y Vulnerabilidades:** Identificación de errores en tiempo de ejecución y fallos de seguridad.
* **Code Smells y Mantenibilidad:** Detección de patrones de código anti-limpios, duplicaciones o complejidad ciclomática elevada.
* **Seguridad (Security Hotspots):** Revisión de potenciales riesgos como exposición de secretos o configuraciones inseguras de FastAPI/JWT.

### Generación de reporte local (para enviar a SonarQube)

Para generar el reporte de cobertura compatible con SonarQube antes de subir los cambios:

```bash
# 1. Ejecutar tests con generación de reporte XML de cobertura
pytest --cov=. --cov-report=xml:coverage.xml

# 2. Ejecutar SonarScanner (requiere sonar-scanner CLI configurado o contenedor Docker)
sonar-scanner \
  -Dsonar.projectKey=global-invoice-metrics \
  -Dsonar.sources=. \
  -Dsonar.python.coverage.reportPaths=coverage.xml \
  -Dsonar.exclusions="tests/**,venv/**"

## Tecnologías

- Python 3.11+ / **FastAPI**
- SQLAlchemy + Psycopg2 (PostgreSQL, modo lectura)
- JWT (mismo secreto que el micro Java)
- Docker / Docker Compose
- Pytest (cobertura mínima 80% en CI)

---

## Contrato con Java y Angular

### Esquema esperado (Java es dueño de la tabla)

```sql
CREATE TABLE invoices (
  id UUID PRIMARY KEY,
  invoice_type VARCHAR(32) NOT NULL, -- NACIONAL | EXPORTACION | GUBERNAMENTAL
  total NUMERIC(19, 2) NOT NULL
);
```

### Evento interno (Java → Python)

Cuando Java persiste una factura, debe notificar a este micro:

`POST /internal/events/invoice-created`

Header: `X-Internal-Key: <INTERNAL_API_KEY>`

```json
{ "invoice_type": "NACIONAL", "total": "119.00" }
```

Eso incrementa el caché y **broadcast** a los dashboards conectados.

### Dashboard (Angular)

- REST (carga inicial o fallback): `GET /api/v1/metrics/by-type`  
  Header: `Authorization: Bearer <JWT>`  
  **Solo rol `ROLE_AUDITOR`**. `ROLE_OPERADOR` recibe 403.
- Tiempo real: `WS /ws/metrics?token=<JWT>`  
  Al conectar llega el snapshot; cada alta de factura llega `{ "event": "metrics_updated", "data": ... }`.

Respuesta:

```json
{
  "by_type": [
    { "invoice_type": "NACIONAL", "total": "119.00", "count": 1 },
    { "invoice_type": "EXPORTACION", "total": "0.00", "count": 0 },
    { "invoice_type": "GUBERNAMENTAL", "total": "0.00", "count": 0 }
  ],
  "grand_total": "119.00",
  "invoice_count": 1
}
```

JWT: claim `role` (o `roles`) con `ROLE_AUDITOR` / `ROLE_OPERADOR`. Mismo `JWT_SECRET` que Java.

---

## Ejecución

### Prerrequisitos

- Red Docker: `docker network create global-invoice-net`
- PostgreSQL del stack (carpeta `mysql/`) ya arriba.

### Variables

Copia `.env.example` a `.env` y alinea `JWT_SECRET` e `INTERNAL_API_KEY` con Java.

### Docker

```bash
docker compose up --build
```

Health: `GET http://localhost:5000/health`

### Swagger / OpenAPI

Con el contenedor arriba:

- Swagger UI: [http://localhost:5000/docs](http://localhost:5000/docs)
- ReDoc: [http://localhost:5000/redoc](http://localhost:5000/redoc)
- Spec: [http://localhost:5000/openapi.json](http://localhost:5000/openapi.json)

En **Authorize**:
1. `BearerJWT` → JWT de Java (`ROLE_AUDITOR` para probar métricas).
2. `InternalKey` → valor de `INTERNAL_API_KEY` para probar el evento de alta.

El WebSocket `/ws/metrics` aparece en la spec; Swagger UI no lo ejecuta.

### Tests

```bash
pip install -r requirements.txt
pytest
```
