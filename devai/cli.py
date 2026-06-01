import click
from devai.detector import detect_stack
from devai.generator import generate_files
from devai.debugger import debug_container

@click.group()
@click.version_option()
def main():
    """devai — AI-powered Docker assistant. No config needed."""
    pass


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def init(path):
    """Analyse ton projet et génère Dockerfile + docker-compose."""
    click.echo(click.style("🔍 Analyse du projet...", fg="cyan"))

    stack = detect_stack(path)
    if not stack:
        click.echo(click.style("❌ Impossible de détecter la stack. Vérifie que tu es dans le bon dossier.", fg="red"))
        raise SystemExit(1)

    click.echo(click.style(f"✅ Stack détectée : {stack['language']} / {', '.join(stack['services'])}", fg="green"))
    click.echo(click.style("⚙️  Génération des fichiers Docker...", fg="cyan"))

    generated = generate_files(path, stack)
    for f in generated:
        click.echo(click.style(f"  ✅ {f} créé", fg="green"))

    click.echo(click.style("\n🚀 Prêt ! Lance avec : docker compose up -d", fg="bright_green", bold=True))


@main.command()
@click.argument("container_name")
def debug(container_name):
    """Analyse les logs d'un container et explique l'erreur."""
    click.echo(click.style(f"🔍 Lecture des logs de '{container_name}'...", fg="cyan"))
    debug_container(container_name)


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def scan(path):
    """Affiche un résumé de la stack détectée sans rien générer."""
    stack = detect_stack(path)
    if not stack:
        click.echo(click.style("❌ Aucune stack détectée.", fg="red"))
        return

    click.echo(click.style("📦 Stack détectée :", fg="cyan", bold=True))
    click.echo(f"  Langage     : {stack['language']}")
    click.echo(f"  Framework   : {stack.get('framework', 'inconnu')}")
    click.echo(f"  Port        : {stack.get('port', 'inconnu')}")
    click.echo(f"  Services    : {', '.join(stack['services']) if stack['services'] else 'aucun'}")
    click.echo(f"  Python ver. : {stack.get('python_version', 'N/A')}")
