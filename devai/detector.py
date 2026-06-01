import os
import re
from pathlib import Path


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
