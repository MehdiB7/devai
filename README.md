# devai

> AI-powered Docker assistant. No config needed.

`devai` analyse ton projet, génère le Dockerfile et le docker-compose, et debug tes containers avec l'IA — le tout en une commande.

## Installation

```bash
pip install stackai-cli
```

> Requiert [Ollama](https://ollama.com) installé et `ollama pull llama3` pour le mode debug AI.

## Utilisation

### `devai init` — Générer les fichiers Docker

```bash
cd mon-projet
stackai init
```

```
🔍 Analyse du projet...
✅ Stack détectée : python / fastapi + postgres + redis
⚙️  Génération des fichiers Docker...
  ✅ Dockerfile créé
  ✅ .dockerignore créé
  ✅ docker-compose.yaml créé

🚀 Prêt ! Lance avec : docker compose up -d
```

### `devai scan` — Voir la stack sans rien générer

```bash
stackai scan
```

```
📦 Stack détectée :
  Langage     : python
  Framework   : fastapi
  Port        : 8000
  Services    : postgres, redis
  Python ver. : 3.11
```

### `devai debug` — Analyser un container en erreur

```bash
stackai debug mon-container
```

```
📋 Derniers logs :
  ─────────────────────────────────────────
  Error: could not connect to postgres...
  ─────────────────────────────────────────

🤖 Analyse IA en cours...

💡 Analyse :
1. PROBLÈME : L'application ne peut pas se connecter à PostgreSQL
2. CAUSE : Le container postgres n'est pas encore prêt au démarrage de l'app
3. FIX : Ajoute `depends_on: [postgres]` dans ton docker-compose.yaml
```

## Stacks supportées

| Langage | Frameworks détectés |
|---------|-------------------|
| Python | FastAPI, Flask, Django, générique |
| Node.js | Express, Next.js, Nuxt.js, React |
| Java | Spring Boot (Maven/Gradle) |
| Go | générique |

## Services auto-détectés

`postgres` · `redis` · `mongodb` · `mysql` · `elasticsearch`

## Prérequis

- Python 3.10+
- Docker installé
- [Ollama](https://ollama.com) + `ollama pull llama3` (pour `devai debug`)

## Licence

MIT
