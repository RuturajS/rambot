import click
import bot
import os

@click.group()
def cli():
    pass

@cli.command()
@click.argument('file_path')
def upload(file_path):
    """Upload an Excel file."""
    if not os.path.exists(file_path):
        click.echo("File not found.")
        return
    
    try:
        hash_id = bot.save_file(file_path, source="CLI")
        click.echo(f"File uploaded successfully. Hash ID: {hash_id}")
    except Exception as e:
        click.echo(f"Error: {e}")

@cli.command()
def list():
    """List all uploaded files."""
    files = bot.list_files()
    if not files:
        click.echo("No files found.")
        return
        
    click.echo(f"{'Hash ID':<20} {'Filename':<30} {'Date':<20}")
    click.echo("-" * 70)
    for f in files:
        click.echo(f"{f['hash_id']:<20} {f['filename']:<30} {f['upload_date']:<20}")

@cli.command()
@click.argument('hash_id')
@click.argument('query')
def query(hash_id, query):
    """Ask a question about an uploaded file using its Hash ID."""
    click.echo("Analyzing...")
    response = bot.analyze_file(hash_id, query)
    click.echo(f"\nResponse:\n{response}")

@cli.command()
@click.argument('hash_id')
def analyze(hash_id):
    """Generate a comprehensive summary of the file."""
    click.echo("Generating summary...")
    response = bot.analyze_file(hash_id, "Please provide a comprehensive summary of this data.")
    click.echo(f"\nSummary:\n{response}")

@cli.command()
@click.argument('hash_id')
@click.argument('instruction')
def edit(hash_id, instruction):
    """Edit an Excel file using AI instructions."""
    click.echo("Editing file...")
    new_hash, msg = bot.edit_file_dataset(hash_id, instruction)
    if new_hash:
        click.echo(f"Success! New file saved with Hash ID: {new_hash}")
    else:
        click.echo(f"Error: {msg}")

if __name__ == '__main__':
    cli()
