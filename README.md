# Microservicio de métricas — Global-Invoice

Servicio de **inteligencia de negocio** para el Dashboard (RF-04). Solo lectura sobre PostgreSQL, caché en memoria y push por WebSocket para que la gráfica se actualice al crear una factura **sin volver a consultar la BD**.

---

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

Si los nombres cambian, ajústalos con `INVOICE_TABLE`, `INVOICE_TYPE_COLUMN` e `INVOICE_TOTAL_COLUMN`.

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
