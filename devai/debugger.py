import subprocess
import click
from devai.ai import ask_ollama


def debug_container(container_name: str):
    """Récupère les logs Docker et les envoie à l'IA pour analyse."""

    # 1. Récupérer les logs
    try:
        result = subprocess.run(
            ["docker", "logs", "--tail", "100", container_name],
            capture_output=True,
            text=True,
            timeout=15,
        )
        logs = result.stdout + result.stderr
    except FileNotFoundError:
        click.echo(click.style("❌ Docker n'est pas installé ou introuvable dans le PATH.", fg="red"))
        return
    except subprocess.TimeoutExpired:
        click.echo(click.style("❌ Timeout lors de la récupération des logs.", fg="red"))
        return

    if not logs.strip():
        click.echo(click.style("⚠️  Aucun log trouvé pour ce container.", fg="yellow"))
        return

    click.echo(click.style("📋 Derniers logs :", fg="cyan"))
    click.echo(click.style("─" * 60, fg="bright_black"))
    # Affiche les 20 dernières lignes pour ne pas surcharger
    lines = logs.strip().splitlines()
    for line in lines[-20:]:
        click.echo(f"  {line}")
    click.echo(click.style("─" * 60, fg="bright_black"))

    # 2. Envoyer à l'IA
    click.echo(click.style("\n🤖 Analyse IA en cours...", fg="cyan"))

    prompt = f"""Tu es un expert Docker et DevOps. Analyse ces logs de container Docker et réponds en français.

LOGS :
{logs[-3000:]}

Réponds avec ce format exact :
1. PROBLÈME : [explication courte du problème]
2. CAUSE : [pourquoi ça arrive]
3. FIX : [commande ou modification exacte à faire]
"""

    response = ask_ollama(prompt)
    if response:
        click.echo(click.style("\n💡 Analyse :", fg="green", bold=True))
        click.echo(response)
    else:
        click.echo(click.style("❌ Impossible de contacter Ollama. Lance-le avec : ollama serve", fg="red"))
