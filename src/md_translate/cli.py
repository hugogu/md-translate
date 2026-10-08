"""Command-line interface for md-translate."""

import sys
from pathlib import Path
import click
from .core import translate_file
from .translators.base import _TRANSLATOR_REGISTRY

@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input_path", type=click.Path(exists=True, dir_okay=True, file_okay=True))
@click.option(
    "-o", "--output", "output_path",
    type=click.Path(),
    help="Output file or directory path. Default appends language suffix or overwrites."
)
@click.option(
    "--engine", "-e",
    default="nllb",
    show_default=True,
    help=f"Translation engine: {', '.join(_TRANSLATOR_REGISTRY.keys())}"
)
@click.option("--from", "-f", "src_lang", default="en", show_default=True, help="Source language code.")
@click.option("--to", "-t", "tgt_lang", default="zh", show_default=True, help="Target language code.")
@click.option("--model", "-m", help="Custom model name or HuggingFace path.")
@click.option("--recursive", "-r", is_flag=True, help="Recursively process markdown files in directory.")
def main(input_path, output_path, engine, src_lang, tgt_lang, model, recursive):
    """Translate Markdown files preserving formulas, code blocks, tables, and links."""
    in_p = Path(input_path)

    extra_kwargs = {}
    if model:
        extra_kwargs["model"] = model

    if in_p.is_file():
        out_p = Path(output_path) if output_path else in_p.with_name(f"{in_p.stem}.{tgt_lang}{in_p.suffix}")
        click.echo(f"Translating {in_p} -> {out_p} [engine={engine}, {src_lang}->{tgt_lang}]...")
        translate_file(in_p, out_p, translator=engine, src_lang=src_lang, tgt_lang=tgt_lang, **extra_kwargs)
        click.echo(click.style(f"✓ Completed: {out_p}", fg="green"))
    elif in_p.is_dir():
        pattern = "**/*.md" if recursive else "*.md"
        files = list(in_p.glob(pattern))
        if not files:
            click.echo(click.style(f"No Markdown files found in {in_p}", fg="yellow"))
            return

        click.echo(f"Found {len(files)} file(s) in {in_p}. Starting batch translation...")
        out_dir = Path(output_path) if output_path else in_p

        for f in files:
            if output_path:
                rel = f.relative_to(in_p)
                dest = out_dir / rel.parent / f"{rel.stem}.{tgt_lang}{rel.suffix}"
            else:
                dest = f.with_name(f"{f.stem}.{tgt_lang}{f.suffix}")

            click.echo(f"Processing: {f.name} -> {dest.name}")
            translate_file(f, dest, translator=engine, src_lang=src_lang, tgt_lang=tgt_lang, **extra_kwargs)

        click.echo(click.style(f"✓ Batch completed. Processed {len(files)} files.", fg="green"))

if __name__ == "__main__":
    main()
