# stackai-cli

> AI-powered Docker assistant. No configuration needed.

`stackai` analyzes your project, generates an optimized Dockerfile and docker-compose, and debugs your containers using a local AI model — all in a single command.

[![PyPI version](https://img.shields.io/pypi/v/stackai-cli.svg)](https://pypi.org/project/stackai-cli/)
[![Python](https://img.shields.io/pypi/pyversions/stackai-cli.svg)](https://pypi.org/project/stackai-cli/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install stackai-cli
```

> `stackai debug` requires [Ollama](https://ollama.com) running locally with `ollama pull llama3`.

## Commands

### `stackai init` — Generate Docker files from your project

```bash
cd my-project
stackai init
```

```
🔍 Analyzing project...
✅ Stack detected: python / fastapi + postgres + redis
⚙️  Generating Docker files...
  ✅ Dockerfile created
  ✅ .dockerignore created
  ✅ docker-compose.yaml created

🚀 Ready! Run: docker compose up -d
```

### `stackai scan` — Inspect detected stack without generating files

```bash
stackai scan
```

```
📦 Stack detected:
  Language    : python
  Framework   : fastapi
  Port        : 8000
  Services    : postgres, redis
  Python ver. : 3.11
```

### `stackai debug` — Analyze a failing container with AI

```bash
stackai debug my-container
```

```
📋 Latest logs:
  ─────────────────────────────────────────
  Error: could not connect to postgres...
  ─────────────────────────────────────────

🤖 Running AI analysis...

💡 Analysis:
1. PROBLEM : The app cannot connect to PostgreSQL
2. CAUSE   : The postgres container is not ready when the app starts
3. FIX     : Add `depends_on: [postgres]` in your docker-compose.yaml
```

## Supported Stacks

| Language | Detected Frameworks |
|----------|-------------------|
| Python   | FastAPI, Flask, Django, generic |
| Node.js  | Express, Next.js, Nuxt.js, React |
| Java     | Spring Boot (Maven / Gradle) |
| Go       | generic |

## Auto-detected Services

`postgres` · `redis` · `mongodb` · `mysql` · `elasticsearch`

## Requirements

- Python 3.10+
- Docker installed and running
- [Ollama](https://ollama.com) + `ollama pull llama3` (only for `stackai debug`)

## Contributing

Pull requests are welcome. For major changes, please open an issue first.

## License

MIT © [El Mehdi Boutahar](https://github.com/MehdiB7)
