import click
from devai.detector import detect_stack
from devai.generator import generate_files
from devai.debugger import debug_container
from devai import __version__

@click.group()
@click.version_option(version=__version__, prog_name="stackai")
def main():
    """stackai — AI-powered Docker assistant. No configuration needed."""
    pass


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def init(path):
    """Analyse ton projet et génère Dockerfile + docker-compose."""
    click.echo(click.style("🔍 Analyzing project...", fg="cyan"))

    stack = detect_stack(path)
    if not stack:
        click.echo(click.style("❌ Could not detect stack. Make sure you are in a project directory.", fg="red"))
        raise SystemExit(1)

    services = ', '.join(stack['services']) if stack['services'] else 'none'
    click.echo(click.style(f"✅ Stack detected: {stack['language']} / {stack.get('framework','generic')} + {services}", fg="green"))
    click.echo(click.style("⚙️  Generating Docker files...", fg="cyan"))

    generated = generate_files(path, stack)
    for f in generated:
        click.echo(click.style(f"  ✅ {f} created", fg="green"))

    click.echo(click.style("\n🚀 Ready! Run: docker compose up -d", fg="bright_green", bold=True))


@main.command()
@click.argument("container_name")
def debug(container_name):
    """Analyse les logs d'un container et explique l'erreur."""
    click.echo(click.style(f"🔍 Reading logs from '{container_name}'...", fg="cyan"))
    debug_container(container_name)


@main.command()
@click.argument("path", default=".", type=click.Path(exists=True))
def scan(path):
    """Affiche un résumé de la stack détectée sans rien générer."""
    stack = detect_stack(path)
    if not stack:
        click.echo(click.style("❌ Aucune stack détectée.", fg="red"))
        return

    click.echo(click.style("📦 Stack detected:", fg="cyan", bold=True))
    click.echo(f"  Language    : {stack['language']}")
    click.echo(f"  Framework   : {stack.get('framework', 'unknown')}")
    click.echo(f"  Port        : {stack.get('port', 'unknown')}")
    click.echo(f"  Services    : {', '.join(stack['services']) if stack['services'] else 'none'}")
    click.echo(f"  Python ver. : {stack.get('python_version', 'N/A')}")
