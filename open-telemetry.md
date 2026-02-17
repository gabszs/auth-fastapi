# OpenTelemetry Python Automatic Instrumentation with FastAPI

Complete guide to automatic instrumentation of Python FastAPI applications using OpenTelemetry, including Pyroscope span profiles, system metrics, and Docker containerization.

## Table of Contents
1. [Understanding OpenTelemetry Instrumentation](#understanding-opentelemetry-instrumentation)
2. [Dependencies](#dependencies)
3. [Instrumentation Methods](#instrumentation-methods)
4. [OpenTelemetry Bootstrap](#opentelemetry-bootstrap)
5. [Environment Configuration](#environment-configuration)
6. [Resource Attributes](#resource-attributes)
7. [Pyroscope Integration](#pyroscope-integration)
8. [Dockerfile Setup](#dockerfile-setup)
9. [Troubleshooting](#troubleshooting)

---

## Understanding OpenTelemetry Instrumentation

### Step-by-Step Instrumentation Flow

When you run an OpenTelemetry-instrumented Python application, the instrumentation process works as follows:

**Step 1: Bootstrap Discovers Installed Libraries**
```bash
opentelemetry-bootstrap -a install
```
This command scans your virtual environment for known libraries and automatically installs corresponding instrumentation packages.

**Step 2: Application Startup with Auto-Instrumentation**
```bash
opentelemetry-instrument uvicorn --host 0.0.0.0 --port 80 app.main:app
```
The `opentelemetry-instrument` command:
- Imports all installed instrumentation packages
- Wraps library entry points before your application code runs
- Intercepts library calls to collect telemetry data
- Requires **zero code changes** in your application

**Step 3: Traces and Metrics are Collected**
- HTTP requests to FastAPI endpoints
- Database queries (SQLAlchemy, asyncpg, etc.)
- External HTTP calls (requests, httpx)
- Async operations (asyncio)
- And more...

**Step 4: Data Exported via OTLP**
All collected data is sent to the OTLP exporter endpoint (configured via `OTEL_EXPORTER_OTLP_ENDPOINT`).

---

## Dependencies

Add these dependencies to your `pyproject.toml`:
```toml
[tool.poetry.dependencies]
python = "^3.13"
fastapi = "^0.104.0"
uvicorn = "^0.24.0"
opentelemetry-distro = ">=0.60b1,<0.61"
opentelemetry-exporter-otlp = ">=1.39.1,<2.0.0"
pyroscope-otel = ">=0.4.1,<0.5.0"
opentelemetry-instrumentation-system-metrics = ">=0.60b1,<0.61"
```

**Key Packages:**
- `opentelemetry-distro`: Meta-package containing all core OpenTelemetry components
- `opentelemetry-exporter-otlp`: Exports traces, metrics, and logs via OTLP
- `pyroscope-otel`: Links traces with continuous profiling data
- `opentelemetry-instrumentation-system-metrics`: Collects system-level metrics (CPU, memory, disk, network) — **Must be explicitly added** (not installed by bootstrap)

---

## Instrumentation Methods

### Method 1: Automatic Instrumentation (Recommended for FastAPI)

Run your application with the `opentelemetry-instrument` command:
```bash
opentelemetry-instrument uvicorn --proxy-headers --host 0.0.0.0 --port 80 app.main:app
```

**How It Works:**
- Automatically instruments FastAPI, HTTP servers, database clients, and other supported libraries
- Wraps library entry points to collect traces
- Requires no code changes in your application

**Instrumentation Enabled Automatically:**
- HTTP server (FastAPI/ASGI/WSGI)
- Database drivers (psycopg2, PyMySQL, SQLAlchemy, etc.)
- Async operations (asyncio)
- Context propagation

### Method 2: Manual Instrumentation (Custom Use Cases)

If you need fine-grained control or custom instrumentation:
```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from pyroscope.otel import PyroscopeSpanProcessor
import pyroscope

# Configure Pyroscope first (required for span profiles)
pyroscope.configure(
    app_name="my-fastapi-service",
    server_address="http://localhost:4040",
    sample_rate=100,
)

# Create and configure TracerProvider
provider = TracerProvider()

# Add Pyroscope processor (links traces with profiles)
provider.add_span_processor(PyroscopeSpanProcessor())

# Add OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="localhost:4317",
    insecure=True,  # Set to False for HTTPS
)
provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

# Set as global tracer provider
trace.set_tracer_provider(provider)

# Use in your FastAPI application
from fastapi import FastAPI

app = FastAPI()

tracer = trace.get_tracer(__name__)

@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    with tracer.start_as_current_span("fetch_user") as span:
        span.set_attribute("user.id", user_id)
        # Your logic here
        return {"id": user_id}
```

---

## OpenTelemetry Bootstrap

### What `opentelemetry-bootstrap` Does

The `opentelemetry-bootstrap -a install` command automatically discovers and installs instrumentation packages for all detected libraries in your environment:
```bash
RUN opentelemetry-bootstrap -a install
```

### Packages Automatically Installed by Bootstrap

The following `opentelemetry-instrumentation-*` packages are discovered and installed automatically:

- `opentelemetry-instrumentation-asyncio`
- `opentelemetry-instrumentation-asyncpg`
- `opentelemetry-instrumentation-asgi`
- `opentelemetry-instrumentation-click`
- `opentelemetry-instrumentation-dbapi`
- `opentelemetry-instrumentation-fastapi`
- `opentelemetry-instrumentation-grpc`
- `opentelemetry-instrumentation-httpx`
- `opentelemetry-instrumentation-logging`
- `opentelemetry-instrumentation-redis`
- `opentelemetry-instrumentation-requests`
- `opentelemetry-instrumentation-sqlite3`
- `opentelemetry-instrumentation-sqlalchemy`
- `opentelemetry-instrumentation-starlette`
- `opentelemetry-instrumentation-threading`
- `opentelemetry-instrumentation-urllib`
- `opentelemetry-instrumentation-wsgi`

> **Note:** `opentelemetry-instrumentation-system-metrics` is **NOT** automatically installed by bootstrap and must be explicitly added to `pyproject.toml`. Once installed, it is automatically enabled with zero-code activation.

### Controlling Bootstrap Behavior

**Option 1: Disable Specific Instrumentations via Environment Variable**

You can disable specific instrumentations at runtime without reinstalling. Use comma-separated values with the instrumentation name (without the `opentelemetry-instrumentation-` prefix):
```bash
# Disable fastapi, asgi, and requests instrumentations
export OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=fastapi,asgi,requests
```

Or in docker-compose:
```yaml
environment:
  OTEL_PYTHON_DISABLED_INSTRUMENTATIONS: "fastapi,asgi,requests"
```

Or in Dockerfile:
```dockerfile
ENV OTEL_PYTHON_DISABLED_INSTRUMENTATIONS="fastapi,asgi,requests"
```

**Supported Instrumentation Names for Disabling:**
```
asyncio, asyncpg, asgi, click, dbapi, fastapi, grpc, httpx, 
logging, redis, requests, sqlite3, sqlalchemy, starlette, 
threading, urllib, wsgi
```

**Option 2: Manual Installation Only (No Bootstrap)**

If you prefer to install only specific instrumentations and skip bootstrap:
```dockerfile
# Instead of: RUN opentelemetry-bootstrap -a install

# Install only what you need:
RUN pip install \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-instrumentation-sqlalchemy \
    opentelemetry-instrumentation-requests \
    opentelemetry-instrumentation-asyncio
```

Then run without bootstrap:
```bash
# Without opentelemetry-bootstrap
opentelemetry-instrument uvicorn app.main:app
```

### Bootstrap vs. Manual Installation

| Aspect | Bootstrap | Manual |
|--------|-----------|--------|
| Automatic discovery | ✅ Yes | ❌ No |
| Image size | Larger (installs ~15+ packages) | Smaller (install only needed) |
| Setup complexity | One command | Must list each package |
| Maintenance | Easy | Requires manual updates |
| Flexibility | Limited control | Full control |
| Runtime disable | Possible via env vars | Not possible |

**When to use Bootstrap:**
- Development and testing environments
- When you're unsure which libraries are used
- Rapid prototyping

**When to use Manual Installation:**
- Production environments where size matters
- Microservices with minimal dependencies
- When you want explicit control over what's installed

---

## Environment Configuration

### .env File Example
```dotenv
# Core OpenTelemetry Configuration
OTEL_SERVICE_NAME="my-fastapi-service"
OTEL_SERVICE_NAMESPACE="production"
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317"
OTEL_EXPORTER_OTLP_INSECURE="true"

# Instrumentation Enablement
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED="true"
OTEL_PYTHON_LOG_LEVEL="INFO"

# Exporters
OTEL_LOGS_EXPORTER="otlp"
OTEL_METRICS_EXPORTER="otlp"
OTEL_TRACES_EXPORTER="otlp"

# Pyroscope Configuration (if using Pyroscope)
PYROSCOPE_SERVER_ADDRESS="http://pyroscope:4040"
PYROSCOPE_AUTH_TOKEN=""
```

### Core OpenTelemetry Configuration Variables
```dotenv
# Service identification
OTEL_SERVICE_NAME="my-fastapi-service"
OTEL_SERVICE_NAMESPACE="production"
# OTEL_SERVICE_NAMESPACE groups related services (production, staging, development)
# All services with the same namespace appear together in observability dashboards

OTEL_SERVICE_VERSION="1.0.0"

# OTLP Exporter Endpoint and Protocol
OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4317"
# OTEL_EXPORTER_OTLP_ENDPOINT is the collector address where traces/metrics are sent
# Format: <protocol>://<host>:<port>
# Common ports: 4317=gRPC, 4318=HTTP/Protobuf
# Port mismatch causes connection errors - verify protocol and port match!

OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
# OTEL_EXPORTER_OTLP_PROTOCOL defines how data is sent
# "grpc"          = gRPC binary protocol (port 4317, more efficient)
# "http/protobuf" = HTTP with Protobuf (port 4318, more compatible)
# IMPORTANT: Protocol must match collector's listening port!

OTEL_EXPORTER_OTLP_INSECURE="true"
# OTEL_EXPORTER_OTLP_INSECURE controls TLS/SSL validation
# "true"  = Do NOT verify SSL certificate (development/self-signed)
# "false" = VERIFY SSL certificate (production with HTTPS)
# In production with HTTPS, set to false or omit

# Individual exporter endpoints (override OTEL_EXPORTER_OTLP_ENDPOINT)
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT="http://localhost:4317"
OTEL_EXPORTER_OTLP_METRICS_ENDPOINT="http://localhost:4317"
OTEL_EXPORTER_OTLP_LOGS_ENDPOINT="http://localhost:4317"
```

### Python-Specific Instrumentation
```dotenv
# Auto-instrumentation for Python
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED="true"
OTEL_PYTHON_LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR

# Disable specific instrumentations (comma-separated, no prefix)
OTEL_PYTHON_DISABLED_INSTRUMENTATIONS="fastapi,asgi,requests"
# Format: names WITHOUT "opentelemetry-instrumentation-" prefix
# Available: asyncio, asyncpg, asgi, click, dbapi, fastapi, grpc, httpx, logging, redis, requests, sqlite3, sqlalchemy, starlette, threading, urllib, wsgi

# Exclude specific URLs from instrumentation
OTEL_INSTRUMENTATION_HTTP_EXCLUDED_URLS="/health,/metrics,/ready"
```

### Exporters Configuration
```dotenv
# Which exporters to use
OTEL_TRACES_EXPORTER="otlp"       # or "jaeger", "zipkin"
OTEL_METRICS_EXPORTER="otlp"      # or "prometheus"
OTEL_LOGS_EXPORTER="otlp"         # or "logging"

# Sampler configuration (optional)
OTEL_TRACES_SAMPLER="parentbased_always_on"  # or "always_off", "always_on"
OTEL_TRACES_SAMPLER_ARG="1.0"     # Sampling rate 0.0-1.0
```

### OTLP Protocol Configuration

#### gRPC Protocol (Default, Recommended)

**For standard gRPC endpoint (port 4317):**
```dotenv
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4317"
OTEL_EXPORTER_OTLP_INSECURE="true"
```

**For gRPC with HTTPS/TLS:**
```dotenv
OTEL_EXPORTER_OTLP_PROTOCOL="grpc"
OTEL_EXPORTER_OTLP_ENDPOINT="https://otel-collector:4317"
OTEL_EXPORTER_OTLP_INSECURE="false"
```

#### HTTP/Protobuf Protocol

**For HTTP endpoint (port 4318):**
```dotenv
OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector:4318"
OTEL_EXPORTER_OTLP_INSECURE="true"
```

**For HTTP with HTTPS:**
```dotenv
OTEL_EXPORTER_OTLP_PROTOCOL="http/protobuf"
OTEL_EXPORTER_OTLP_ENDPOINT="https://otel-collector:4318"
OTEL_EXPORTER_OTLP_INSECURE="false"
```

#### Important Notes

- **HTTPS without Certificate Validation:**
```dotenv
  OTEL_EXPORTER_OTLP_ENDPOINT="https://otel-collector:4317"
  OTEL_EXPORTER_OTLP_INSECURE="true"
```
  **Not recommended for production** but useful for self-signed certificates in development.

- **Port Selection:**
  - Port `4317`: gRPC protocol
  - Port `4318`: HTTP/Protobuf protocol

- **Protocol Mismatch Error:**
```
  ✅ CORRECT:   gRPC protocol → port 4317
  ✅ CORRECT:   HTTP protocol → port 4318
  ❌ WRONG:     gRPC protocol → port 4318
  ❌ WRONG:     HTTP protocol → port 4317
```

---

## Resource Attributes

### What are Resource Attributes?

Resource attributes provide metadata about your service (version, environment, owner, deployment info) that appear in all traces and metrics. They enable filtering and grouping in observability platforms.

### Configuration via Environment Variables

Set the `OTEL_RESOURCE_ATTRIBUTES` environment variable with comma-separated key-value pairs:
```bash
export OTEL_RESOURCE_ATTRIBUTES="service.namespace=production,service.environment=production,service.host=app-01,service.version=1.0.0"
```

### Complete Example with All Fields
```dotenv
OTEL_RESOURCE_ATTRIBUTES="service.namespace=${OTEL_SERVICE_NAMESPACE},service.environment=${OTEL_SERVICE_NAMESPACE},service.host=${SERVICE_HOST},service.version=${SERVICE_VERSION},service.build.git_hash=${COMMIT_HASH},service.owner.name=${SERVICE_OWNER_NAME},service.owner.url=${SERVICE_OWNER_URL},service.owner.contact=${SERVICE_OWNER_CONTACT},service.owner.discord=${SERVICE_OWNER_DISCORD},service.build.git_branch=${COMMIT_BRANCH},service.build.deployment.user=${DEPLOYMENT_USER},service.build.deployment.trigger=${DEPLOYMENT_TRIGGER}"
```

### Individual Attributes Explained

| Attribute | Example | Purpose |
|-----------|---------|---------|
| `service.namespace` | `production` | Environment or deployment namespace |
| `service.environment` | `production` | Environment name |
| `service.host` | `app-01` | Physical or logical host identifier |
| `service.version` | `1.0.0` | Application semantic version |
| `service.build.git_hash` | `abc123def456` | Git commit SHA |
| `service.build.git_branch` | `main` | Git branch name |
| `service.build.deployment.user` | `ci-user` | User who triggered deployment |
| `service.build.deployment.trigger` | `github-actions` | Deployment trigger source |
| `service.owner.name` | `Backend Team` | Team responsible |
| `service.owner.url` | `https://example.com/team` | Team website or documentation |
| `service.owner.contact` | `backend@example.com` | Primary contact email |
| `service.owner.discord` | `channel-id` | Discord channel for alerts |

### Concatenating Values with Environment Variables
```bash
# In your deployment script or docker-compose:
export OTEL_RESOURCE_ATTRIBUTES="service.namespace=production,service.host=$(hostname),service.version=$(cat VERSION),service.build.git_hash=$(git rev-parse HEAD)"

# Or with Docker:
docker run \
  -e OTEL_RESOURCE_ATTRIBUTES="service.namespace=production,service.host=docker-host,service.version=1.0.0,service.build.git_hash=$(git rev-parse HEAD)" \
  my-app:latest
```

---

## Pyroscope Integration

### Pyroscope Configuration in Application

Add this to your `app/main.py` or `app/config.py`:
```python
import os
import pyroscope
from pyroscope.otel import PyroscopeSpanProcessor
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

# Configure Pyroscope BEFORE creating any spans
pyroscope.configure(
    app_name=os.getenv("OTEL_SERVICE_NAME", "app"), # service.name
    server_address="http://localhost:4040", # pyroscope URL
    
)

# Grafana Cloud setup (uncomment and update with your credentials)
# pyroscope_configure(
#     app_name="my-app",
#     server_address="https://pyroscope-blocks-prod-us-central-1.grafana-cloud.com/prom/push",
#     auth_token="<your-grafana-cloud-token>",
#     basic_auth_username="<your-username>",  # Optional: username for basic auth (Grafana Cloud)
#     basic_auth_password="<your-password>",  # Optional: password for basic auth (Grafana Cloud)
#     sample_rate=100,
# )

# Register PyroscopeSpanProcessor
if hasattr(trace, 'get_tracer_provider'):
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.add_span_processor(PyroscopeSpanProcessor())
```

### Using Auto-Instrumentation with Pyroscope

When using `opentelemetry-instrument`, you still need to manually initialize Pyroscope in your code (as shown above). The automatic instrumentation does not handle Pyroscope setup.

### Pyroscope Base Image Requirements

**Wolfi Base (Recommended for Pyroscope, 230mb final size):**
```dockerfile
FROM cgr.dev/chainguard/wolfi-base as runtime
RUN apk add --no-cache python-3.13
# only latest python images are freely available at cgr
# Includes libgc - works with Pyroscope
```

**Alpine Base (NOT Compatible with Pyroscope, 180mb final size):**
```dockerfile
FROM python:3.13-alpine as runtime
# Missing libgc - Pyroscope will fail to initialize
```

If you use Alpine without Pyroscope, remove `pyroscope-otel` from dependencies.

---

## Dockerfile Setup

### Multi-Stage Build with Poetry
```dockerfile
FROM cgr.dev/chainguard/wolfi-base as builder

RUN apk add --no-cache python-3.13 py3.13-pip poetry

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /app/

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --without dev --no-root

ENV PATH="/app/.venv/bin:$PATH"

# Install OpenTelemetry instrumentation packages
RUN opentelemetry-bootstrap -a install

FROM cgr.dev/chainguard/wolfi-base as runtime

RUN apk add --no-cache python-3.13

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY app ./app
COPY pyproject.toml poetry.lock ./
COPY migrations ./migrations
COPY alembic.ini ./

EXPOSE 80

CMD [ "sh", "-c", "alembic upgrade head && opentelemetry-instrument uvicorn --proxy-headers --host 0.0.0.0 --port 80 app.main:app"]
```

### Important Notes on Base Images

**Wolfi Base Image (Current):**
- Includes `libgc` (garbage collector), required by Pyroscope
- Suitable for applications requiring continuous profiling
- Slightly larger footprint than Alpine

**Alpine Image (Lightweight Alternative):**
If you **do not use Pyroscope**, you can use Alpine for significantly smaller images:
```dockerfile
FROM cgr.dev/chainguard/alpine:latest as runtime

RUN apk add --no-cache python3

# ... rest of Dockerfile
```

**Why Pyroscope requires libgc:**
Pyroscope's profiler uses garbage collection information to correlate profiling data with application behavior. The `libgc` library provides these capabilities. Without it, Pyroscope initialization will fail.

---

## Troubleshooting

### Issue: Spans not appearing in backend

**Checklist:**
1. Verify `OTEL_EXPORTER_OTLP_ENDPOINT` is correct
2. Verify `OTEL_EXPORTER_OTLP_PROTOCOL` matches collector port (grpc→4317, http→4318)
3. Check network connectivity: `curl http://otel-collector:4317`
4. Verify trace exporter is enabled: `OTEL_TRACES_EXPORTER="otlp"`
5. Check application logs for export errors

**Debug Command:**
```bash
# Add verbose logging
export OTEL_PYTHON_LOG_LEVEL="DEBUG"
opentelemetry-instrument python app.py
```

### Issue: Pyroscope integration not working

**Error:** `pyroscope.profile.id` not in span attributes

**Solution:**
1. Ensure Pyroscope is configured BEFORE creating any spans
2. Verify `PyroscopeSpanProcessor` is registered:
```python
   provider.add_span_processor(PyroscopeSpanProcessor())
```
3. Check Pyroscope server is running and accessible
4. Verify base image includes `libgc` (use Wolfi, not Alpine)

### Issue: `libgc` not found error with Pyroscope

**Error:** `libgc: No such file or directory`

**Solution:**
Use Wolfi base image instead of Alpine:
```dockerfile
FROM cgr.dev/chainguard/wolfi-base as runtime
RUN apk add --no-cache python-3.13
```

### Issue: System metrics not being collected

**Error:** `system.cpu.*` and `system.memory.*` metrics missing

**Solution:**
1. Install system metrics package:
```bash
   pip install opentelemetry-instrumentation-system-metrics
```
2. Or include in dependencies:
```toml
   opentelemetry-instrumentation-system-metrics = ">=0.60b1,<0.61"
```
3. Run with `opentelemetry-bootstrap -a install`
4. Verify exporter is enabled: `OTEL_METRICS_EXPORTER="otlp"`

### Issue: Certificate validation errors with HTTPS

**Error:** `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions:**

For self-signed certificates in development:
```dotenv
OTEL_EXPORTER_OTLP_INSECURE="true"
```

For proper HTTPS in production:
```dotenv
OTEL_EXPORTER_OTLP_INSECURE="false"
OTEL_EXPORTER_OTLP_CERTIFICATE="/etc/ssl/certs/ca-bundle.crt"
```

### Issue: High memory usage with bootstrap

**Cause:** `opentelemetry-bootstrap` installs many instrumentations

**Solutions:**

Option 1: Install only needed instrumentations
```dockerfile
RUN pip install \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-instrumentation-sqlalchemy
```

Option 2: Disable unused instrumentations at runtime
```dotenv
OTEL_PYTHON_DISABLED_INSTRUMENTATIONS="asyncio,click,grpc,httpx,redis,sqlite3,starlette,threading,urllib"
```

### Issue: Bootstrap takes too long to run

**Cause:** Bootstrap scans environment and downloads many packages

**Solution:**
Use manual installation with cached Docker layers:
```dockerfile
RUN pip install \
    opentelemetry-instrumentation-fastapi \
    opentelemetry-instrumentation-sqlalchemy \
    --no-cache-dir
```

---

## Quick Start Checklist

- [ ] Add dependencies to `pyproject.toml`
- [ ] Add Pyroscope configuration to app startup
- [ ] Set `OTEL_SERVICE_NAME` and `OTEL_EXPORTER_OTLP_ENDPOINT`
- [ ] Set `OTEL_EXPORTER_OTLP_PROTOCOL` (grpc or http/protobuf)
- [ ] Run with `opentelemetry-instrument` command
- [ ] Verify traces appear in observability backend
- [ ] Verify `pyroscope.profile.id` in spans (if using Pyroscope)
- [ ] Configure resource attributes for service metadata
- [ ] Test protocol matching (gRPC→4317, HTTP→4318)

## References

- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [OpenTelemetry Python Getting Started](https://opentelemetry.io/docs/instrumentation/python/getting-started/)
- [Pyroscope Span Profiles](https://grafana.com/docs/pyroscope/latest/configure-client/trace-span-profiles/)
- [OTLP Protocol Specification](https://opentelemetry.io/docs/specs/otlp/)
- [Chainguard Images](https://www.chainguard.dev/chainguard-images)