import os
import re
import json
from pathlib import Path


# ---------------------------------------------------------------------------
# SERVICE MAP  dep_name → [service_ids]
# A single dependency can imply multiple services.
# ---------------------------------------------------------------------------
SERVICE_MAP: dict[str, list[str]] = {
    # ── Relational databases ──────────────────────────────────────────────
    "psycopg2": ["postgres"],       "psycopg2-binary": ["postgres"],
    "asyncpg": ["postgres"],        "sqlalchemy": ["postgres"],
    "alembic": ["postgres"],        "databases": ["postgres"],
    "tortoise-orm": ["postgres"],   "peewee": ["postgres"],
    "dbt-core": ["postgres"],       "dbt-postgres": ["postgres"],
    "dbt-spark": ["spark"],         "dbt-bigquery": [],
    "pymysql": ["mysql"],           "mysql-connector-python": ["mysql"],
    "aiomysql": ["mysql"],
    "cx-oracle": ["oracle"],        "oracledb": ["oracle"],
    "pyodbc": ["mssql"],            "pymssql": ["mssql"],
    "psycopg": ["postgres"],

    # ── NoSQL ─────────────────────────────────────────────────────────────
    "pymongo": ["mongodb"],         "motor": ["mongodb"],
    "mongoengine": ["mongodb"],     "beanie": ["mongodb"],
    "redis": ["redis"],             "aioredis": ["redis"],
    "redis-py": ["redis"],          "coredis": ["redis"],
    "celery": ["redis"],            "dramatiq": ["redis"],
    "rq": ["redis"],
    "cassandra-driver": ["cassandra"],
    "aiofiles": [],

    # ── Search & Analytics ────────────────────────────────────────────────
    "elasticsearch": ["elasticsearch"],
    "elasticsearch-dsl": ["elasticsearch"],
    "opensearch-py": ["opensearch"],
    "opensearchpy": ["opensearch"],
    "solr": ["solr"],
    "clickhouse-driver": ["clickhouse"],
    "clickhouse-connect": ["clickhouse"],

    # ── Streaming / Messaging ─────────────────────────────────────────────
    "kafka-python": ["kafka"],      "confluent-kafka": ["kafka"],
    "aiokafka": ["kafka"],          "faust": ["kafka"],
    "pika": ["rabbitmq"],           "aio-pika": ["rabbitmq"],
    "kombu": ["rabbitmq"],
    "nats-py": ["nats"],

    # ── Object Storage / Cloud ────────────────────────────────────────────
    "boto3": ["minio"],             "botocore": ["minio"],
    "s3fs": ["minio"],              "s3transfer": ["minio"],
    "minio": ["minio"],
    "google-cloud-storage": [],     "azure-storage-blob": [],

    # ── Big Data / Spark ──────────────────────────────────────────────────
    "pyspark": ["spark"],           "delta-spark": ["spark"],
    "spark": ["spark"],

    # ── Streaming / Real-time ─────────────────────────────────────────────
    "pyflink": ["flink"],           "apache-flink": ["flink"],

    # ── Orchestration ─────────────────────────────────────────────────────
    "apache-airflow": ["airflow", "postgres"],
    "airflow": ["airflow", "postgres"],
    "prefect": ["prefect"],
    "dagster": ["dagster", "postgres"],
    "luigi": [],

    # ── ML / AI ───────────────────────────────────────────────────────────
    "mlflow": ["mlflow"],
    "torch": [],                    "tensorflow": [],
    "onnxruntime": [],              "triton": [],

    # ── Tracing / Monitoring ──────────────────────────────────────────────
    "opentelemetry-sdk": ["jaeger"],
    "prometheus-client": ["prometheus"],
    "grafana": ["grafana"],

    # ── Web frameworks (no extra service needed) ──────────────────────────
    "fastapi": [], "flask": [], "django": [], "tornado": [],
    "aiohttp": [], "starlette": [], "litestar": [],
}

# ---------------------------------------------------------------------------
# IMPORT → dep alias (for scanning .py source files)
# ---------------------------------------------------------------------------
IMPORT_TO_DEP: dict[str, str] = {
    "psycopg2": "psycopg2",        "asyncpg": "asyncpg",
    "sqlalchemy": "sqlalchemy",    "alembic": "alembic",
    "pymysql": "pymysql",          "pymongo": "pymongo",
    "motor": "motor",              "redis": "redis",
    "celery": "celery",            "kafka": "kafka-python",
    "confluent_kafka": "confluent-kafka", "aiokafka": "aiokafka",
    "pika": "pika",                "aio_pika": "aio-pika",
    "boto3": "boto3",              "botocore": "botocore",
    "s3fs": "s3fs",                "minio": "minio",
    "pyspark": "pyspark",          "delta": "delta-spark",
    "airflow": "apache-airflow",   "prefect": "prefect",
    "dagster": "dagster",          "mlflow": "mlflow",
    "elasticsearch": "elasticsearch",
    "opensearchpy": "opensearch-py",
    "clickhouse_driver": "clickhouse-driver",
    "cassandra": "cassandra-driver",
    "faust": "faust",              "pyflink": "pyflink",
    "torch": "torch",              "tensorflow": "tensorflow",
    "prometheus_client": "prometheus-client",
    "opentelemetry": "opentelemetry-sdk",
    "dbt": "dbt-core",
}

# Framework detection: import name → (framework_label, default_port)
FRAMEWORK_MAP: dict[str, tuple[str, int]] = {
    "fastapi": ("fastapi", 8000),   "uvicorn": ("fastapi", 8000),
    "flask": ("flask", 5000),       "django": ("django", 8000),
    "tornado": ("tornado", 8888),   "aiohttp": ("aiohttp", 8080),
    "starlette": ("starlette", 8000), "litestar": ("litestar", 8000),
    "express": ("express", 3000),   "next": ("nextjs", 3000),
    "nuxt": ("nuxtjs", 3000),
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def detect_stack(project_path: str) -> dict | None:
    path = Path(project_path)

    if (path / "requirements.txt").exists() or (path / "pyproject.toml").exists():
        return _detect_python(path)
    if (path / "package.json").exists():
        return _detect_node(path)
    if (path / "pom.xml").exists() or (path / "build.gradle").exists():
        return _detect_java(path)
    if (path / "go.mod").exists():
        return _detect_go(path)
    return None


# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------

def _detect_python(path: Path) -> dict:
    deps = _read_python_deps(path)
    deps |= _scan_python_imports(path)   # enrich with source scan
    deps |= _read_env_hints(path)        # enrich with .env hints

    framework, port = _detect_framework(deps)
    services = _deps_to_services(deps)
    python_version = _detect_python_version(path)
    dep_file = "requirements.txt" if (path / "requirements.txt").exists() else "pyproject.toml"

    return {
        "language": "python",
        "framework": framework,
        "port": port,
        "services": services,
        "python_version": python_version,
        "dep_file": dep_file,
        "raw_deps": sorted(deps),
    }


def _read_python_deps(path: Path) -> set[str]:
    """Read requirements.txt and/or pyproject.toml."""
    deps: set[str] = set()

    req = path / "requirements.txt"
    if req.exists():
        for line in req.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            # strip version specifiers
            name = re.split(r"[>=<!;\[]", line)[0].strip().lower()
            if name:
                deps.add(name)

    pyproject = path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text(encoding="utf-8", errors="ignore")
        for m in re.finditer(r'"([a-zA-Z0-9_\-]+)\s*[>=<!]', content):
            deps.add(m.group(1).lower())

    return deps


def _scan_python_imports(path: Path) -> set[str]:
    """Scan .py files for import statements and map to dep names."""
    found: set[str] = set()
    py_files = list(path.rglob("*.py"))[:200]  # cap at 200 files

    import_re = re.compile(
        r"^(?:import|from)\s+([a-zA-Z0-9_]+)", re.MULTILINE
    )
    for f in py_files:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            for m in import_re.finditer(content):
                root = m.group(1).lower()
                if root in IMPORT_TO_DEP:
                    found.add(IMPORT_TO_DEP[root])
        except OSError:
            pass
    return found


def _read_env_hints(path: Path) -> set[str]:
    """Infer services from .env or .env.example variable names."""
    hints: set[str] = set()
    for fname in [".env", ".env.example", ".env.sample"]:
        env_file = path / fname
        if not env_file.exists():
            continue
        content = env_file.read_text(encoding="utf-8", errors="ignore").upper()
        if "POSTGRES" in content or "DATABASE_URL" in content:
            hints.add("psycopg2")
        if "REDIS" in content:
            hints.add("redis")
        if "MONGO" in content:
            hints.add("pymongo")
        if "KAFKA" in content:
            hints.add("kafka-python")
        if "MINIO" in content or "S3_ENDPOINT" in content or "AWS_" in content:
            hints.add("boto3")
        if "SPARK" in content:
            hints.add("pyspark")
        if "AIRFLOW" in content:
            hints.add("apache-airflow")
        if "MLFLOW" in content:
            hints.add("mlflow")
        if "ELASTICSEARCH" in content:
            hints.add("elasticsearch")
    return hints


# ---------------------------------------------------------------------------
# Node.js
# ---------------------------------------------------------------------------

def _detect_node(path: Path) -> dict:
    pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
    all_deps = {
        **pkg.get("dependencies", {}),
        **pkg.get("devDependencies", {}),
    }
    deps = {k.lower() for k in all_deps}

    framework, port = _detect_framework(deps)
    services = _deps_to_services(deps)

    return {
        "language": "nodejs",
        "framework": framework,
        "port": port,
        "services": services,
        "python_version": None,
        "dep_file": "package.json",
        "raw_deps": sorted(deps),
    }


# ---------------------------------------------------------------------------
# Java / Go
# ---------------------------------------------------------------------------

def _detect_java(path: Path) -> dict:
    content = ""
    for f in ["pom.xml", "build.gradle"]:
        p = path / f
        if p.exists():
            content = p.read_text(encoding="utf-8", errors="ignore").lower()
            break

    services = []
    if "postgresql" in content or "postgres" in content:
        services.append("postgres")
    if "mysql" in content:
        services.append("mysql")
    if "mongodb" in content or "mongo" in content:
        services.append("mongodb")
    if "redis" in content:
        services.append("redis")
    if "kafka" in content:
        services.append("kafka")
    if "elasticsearch" in content:
        services.append("elasticsearch")

    return {
        "language": "java",
        "framework": "spring-boot",
        "port": 8080,
        "services": services,
        "python_version": None,
        "dep_file": "pom.xml" if (path / "pom.xml").exists() else "build.gradle",
        "raw_deps": [],
    }


def _detect_go(path: Path) -> dict:
    content = (path / "go.mod").read_text(encoding="utf-8", errors="ignore").lower()
    services = []
    if "postgres" in content or "pgx" in content:
        services.append("postgres")
    if "mongo" in content:
        services.append("mongodb")
    if "redis" in content:
        services.append("redis")
    if "kafka" in content:
        services.append("kafka")

    return {
        "language": "go",
        "framework": "generic",
        "port": 8080,
        "services": services,
        "python_version": None,
        "dep_file": "go.mod",
        "raw_deps": [],
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _deps_to_services(deps: set[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for dep in deps:
        for svc in SERVICE_MAP.get(dep, []):
            if svc and svc not in seen:
                seen.add(svc)
                result.append(svc)
    return result


def _detect_framework(deps: set[str]) -> tuple[str, int]:
    for dep, (fw, port) in FRAMEWORK_MAP.items():
        if dep in deps:
            return fw, port
    return "generic", 8000


def _detect_python_version(path: Path) -> str:
    for f in [".python-version", "runtime.txt"]:
        p = path / f
        if p.exists():
            m = re.search(r"3\.\d+", p.read_text())
            if m:
                return m.group()
    pyproject = path / "pyproject.toml"
    if pyproject.exists():
        m = re.search(r'python_requires\s*=\s*">=\s*(3\.\d+)"', pyproject.read_text())
        if m:
            return m.group(1)
    return "3.11"



# Mapping dépendance → service(s) Docker requis
# Un service peut en impliquer plusieurs (ex: airflow → airflow + postgres)
SERVICE_HINTS = {
    # Databases
    "psycopg2": ["postgres"],
    "asyncpg": ["postgres"],
    "sqlalchemy": ["postgres"],
    "pymongo": ["mongodb"],
    "motor": ["mongodb"],
    "mysql-connector": ["mysql"],
    "pymysql": ["mysql"],
    # Cache / Queue
    "redis": ["redis"],
    "celery": ["redis"],
    # Search
    "elasticsearch": ["elasticsearch"],
    # Streaming
    "kafka": ["kafka"],
    # Object storage
    "boto3": ["minio"],
    "s3fs": ["minio"],
    # Big Data
    "pyspark": ["spark"],
    "delta-spark": ["spark"],
    "pyflink": ["flink"],
    # Orchestration (Airflow implique postgres)
    "apache-airflow": ["airflow", "postgres"],
    "airflow": ["airflow", "postgres"],
}

# Mapping dépendance → framework
FRAMEWORK_HINTS = {
    "fastapi": ("fastapi", 8000),
    "uvicorn": ("fastapi", 8000),
    "flask": ("flask", 5000),
    "django": ("django", 8000),
    "tornado": ("tornado", 8888),
    "aiohttp": ("aiohttp", 8080),
}


def detect_stack(project_path: str) -> dict | None:
    path = Path(project_path)

    # --- Python ---
    req_file = path / "requirements.txt"
    pyproject = path / "pyproject.toml"
    if req_file.exists() or pyproject.exists():
        return _detect_python(path, req_file if req_file.exists() else pyproject)

    # --- Node.js ---
    if (path / "package.json").exists():
        return _detect_node(path)

    # --- Java ---
    if (path / "pom.xml").exists() or (path / "build.gradle").exists():
        return _detect_java(path)

    # --- Go ---
    if (path / "go.mod").exists():
        return _detect_go(path)

    return None


def _detect_python(path: Path, dep_file: Path) -> dict:
    content = dep_file.read_text(encoding="utf-8", errors="ignore").lower()
    deps = [line.split("==")[0].split(">=")[0].strip() for line in content.splitlines() if line.strip() and not line.startswith("#")]

    framework = "generic"
    port = 8000
    for dep, (fw, p) in FRAMEWORK_HINTS.items():
        if dep in deps:
            framework = fw
            port = p
            break

    services = list({s for dep in deps if dep in SERVICE_HINTS for s in SERVICE_HINTS[dep]})

    python_version = _detect_python_version(path)

    return {
        "language": "python",
        "framework": framework,
        "port": port,
        "services": services,
        "python_version": python_version,
        "dep_file": dep_file.name,
    }


def _detect_node(path: Path) -> dict:
    import json
    pkg = json.loads((path / "package.json").read_text(encoding="utf-8"))
    deps = list(pkg.get("dependencies", {}).keys()) + list(pkg.get("devDependencies", {}).keys())
    deps_lower = [d.lower() for d in deps]

    framework = "express"
    port = 3000
    if "next" in deps_lower:
        framework = "nextjs"
        port = 3000
    elif "nuxt" in deps_lower:
        framework = "nuxtjs"
        port = 3000
    elif "react" in deps_lower:
        framework = "react"
        port = 3000

    services = list({s for dep in deps_lower if dep in SERVICE_HINTS for s in SERVICE_HINTS[dep]})

    return {
        "language": "nodejs",
        "framework": framework,
        "port": port,
        "services": services,
        "python_version": None,
        "dep_file": "package.json",
    }


def _detect_java(path: Path) -> dict:
    return {
        "language": "java",
        "framework": "spring-boot",
        "port": 8080,
        "services": [],
        "python_version": None,
        "dep_file": "pom.xml" if (path / "pom.xml").exists() else "build.gradle",
    }


def _detect_go(path: Path) -> dict:
    return {
        "language": "go",
        "framework": "generic",
        "port": 8080,
        "services": [],
        "python_version": None,
        "dep_file": "go.mod",
    }


def _detect_python_version(path: Path) -> str:
    """Cherche la version Python dans .python-version, pyproject.toml ou runtime.txt."""
    for f in [".python-version", "runtime.txt"]:
        p = path / f
        if p.exists():
            content = p.read_text().strip()
            match = re.search(r"3\.\d+", content)
            if match:
                return match.group()

    pyproject = path / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        match = re.search(r'python_requires\s*=\s*">=\s*(3\.\d+)"', content)
        if match:
            return match.group(1)

    return "3.11"  # défaut
