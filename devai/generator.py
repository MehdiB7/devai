from pathlib import Path


DOCKERIGNORE = """\
__pycache__/
*.pyc
*.pyo
.env
.venv
venv/
.git/
.gitignore
*.log
.DS_Store
node_modules/
dist/
build/
"""

# ──────────────────────────────────────────
# DOCKERFILE TEMPLATES
# ──────────────────────────────────────────

PYTHON_DOCKERFILE = """\
FROM python:{python_version}-slim

WORKDIR /app

# Installer les dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copier et installer les dépendances Python
COPY {dep_file} .
RUN pip install --no-cache-dir -r {dep_file}

# Copier le code source
COPY . .

EXPOSE {port}

CMD {cmd}
"""

NODE_DOCKERFILE = """\
FROM node:20-slim

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE {port}

CMD ["node", "index.js"]
"""

JAVA_DOCKERFILE = """\
FROM maven:3.9-eclipse-temurin-17 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline
COPY src ./src
RUN mvn package -DskipTests

FROM eclipse-temurin:17-jre-slim
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
CMD ["java", "-jar", "app.jar"]
"""

GO_DOCKERFILE = """\
FROM golang:1.22-alpine AS build
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN go build -o main .

FROM alpine:latest
WORKDIR /app
COPY --from=build /app/main .
EXPOSE 8080
CMD ["./main"]
"""

# ──────────────────────────────────────────
# SERVICE TEMPLATES pour docker-compose
# ──────────────────────────────────────────

SERVICE_TEMPLATES = {
    "postgres": """\
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: appdb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
""",
    "redis": """\
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
""",
    "mongodb": """\
  mongodb:
    image: mongo:7
    environment:
      MONGO_INITDB_ROOT_USERNAME: user
      MONGO_INITDB_ROOT_PASSWORD: password
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
""",
    "mysql": """\
  mysql:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: appdb
      MYSQL_USER: user
      MYSQL_PASSWORD: password
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
""",
    "elasticsearch": """\
  elasticsearch:
    image: elasticsearch:8.13.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    ports:
      - "9200:9200"
""",
    "minio": """\
  minio:
    image: minio/minio:latest
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: server /data --console-address ":9001"
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
""",
    "airflow": """\
  airflow-webserver:
    image: apache/airflow:2.8.1-python3.11
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    volumes:
      - ./dags:/opt/airflow/dags
    ports:
      - "8080:8080"
    command: >
      bash -c "airflow db migrate && airflow users create --username admin --password admin --firstname Admin --lastname User --role Admin --email admin@example.com; airflow webserver"
    depends_on:
      - postgres

  airflow-scheduler:
    image: apache/airflow:2.8.1-python3.11
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres:5432/airflow
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    volumes:
      - ./dags:/opt/airflow/dags
    command: airflow scheduler
    depends_on:
      - postgres
""",

    "spark": """\
  spark-master:
    image: bitnami/spark:3.5
    environment:
      - SPARK_MODE=master
      - SPARK_MASTER_HOST=spark-master
    ports:
      - "7077:7077"
      - "8081:8080"

  spark-worker:
    image: bitnami/spark:3.5
    environment:
      - SPARK_MODE=worker
      - SPARK_MASTER_URL=spark://spark-master:7077
      - SPARK_WORKER_MEMORY=2g
      - SPARK_WORKER_CORES=2
    depends_on:
      - spark-master
""",
    "flink": """\
  flink-jobmanager:
    image: flink:1.18-scala_2.12
    command: jobmanager
    ports:
      - "8082:8081"
    environment:
      - JOB_MANAGER_RPC_ADDRESS=flink-jobmanager

  flink-taskmanager:
    image: flink:1.18-scala_2.12
    command: taskmanager
    depends_on:
      - flink-jobmanager
    environment:
      - JOB_MANAGER_RPC_ADDRESS=flink-jobmanager
""",
}

VOLUME_NAMES = {
    "postgres": "postgres_data",
    "mongodb": "mongo_data",
    "mysql": "mysql_data",
    "minio": "minio_data",
}

FRAMEWORK_CMDS = {
    "fastapi": '["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "{port}"]',
    "flask": '["flask", "run", "--host=0.0.0.0", "--port={port}"]',
    "django": '["python", "manage.py", "runserver", "0.0.0.0:{port}"]',
    "generic": '["python", "main.py"]',
}


def generate_files(project_path: str, stack: dict) -> list[str]:
    path = Path(project_path)
    generated = []

    # Dockerfile
    dockerfile_content = _build_dockerfile(stack)
    _write(path / "Dockerfile", dockerfile_content)
    generated.append("Dockerfile")

    # .dockerignore
    _write(path / ".dockerignore", DOCKERIGNORE)
    generated.append(".dockerignore")

    # docker-compose.yaml (seulement si services détectés ou toujours utile)
    compose_content = _build_compose(stack)
    _write(path / "docker-compose.yaml", compose_content)
    generated.append("docker-compose.yaml")

    return generated


def _build_dockerfile(stack: dict) -> str:
    lang = stack["language"]
    port = stack["port"]

    if lang == "python":
        cmd = FRAMEWORK_CMDS.get(stack.get("framework", "generic"), FRAMEWORK_CMDS["generic"])
        cmd = cmd.replace("{port}", str(port))
        return PYTHON_DOCKERFILE.format(
            python_version=stack.get("python_version", "3.11"),
            dep_file=stack.get("dep_file", "requirements.txt"),
            port=port,
            cmd=cmd,
        )
    elif lang == "nodejs":
        return NODE_DOCKERFILE.format(port=port)
    elif lang == "java":
        return JAVA_DOCKERFILE
    elif lang == "go":
        return GO_DOCKERFILE
    else:
        return f"FROM ubuntu:22.04\nWORKDIR /app\nCOPY . .\nEXPOSE {port}\n"


def _build_compose(stack: dict) -> str:
    lang = stack["language"]
    port = stack["port"]
    services = stack.get("services", [])
    framework = stack.get("framework", "generic")

    # Depends_on
    depends = ""
    if services:
        depends = "\n    depends_on:\n" + "".join(f"      - {s}\n" for s in services)

    app_service = f"""\
  app:
    build: .
    ports:
      - "{port}:{port}"
    env_file:
      - .env{depends}
"""

    extra_services = "".join(SERVICE_TEMPLATES.get(s, "") for s in services)

    volumes_needed = [VOLUME_NAMES[s] for s in services if s in VOLUME_NAMES]
    volumes_block = ""
    if volumes_needed:
        volumes_block = "\nvolumes:\n" + "".join(f"  {v}:\n" for v in volumes_needed)

    return f"""\
version: '3.9'

services:
{app_service}
{extra_services}{volumes_block}"""


def _write(filepath: Path, content: str):
    filepath.write_text(content, encoding="utf-8")
