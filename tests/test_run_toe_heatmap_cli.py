from __future__ import annotations

from pathlib import Path

from scripts import run_toe_heatmap_with_evidence as cli


def test_cli_parser_defaults():
    parser = cli.create_parser()
    args = parser.parse_args([])

    assert args.config == "configs/rex_simuniverse.yaml"
    assert args.corpus == "corpora/REx.SimUniverseCorpus.v0.2.json"
    assert args.output is None
    assert args.html_output is None
    assert args.notebook_output is None
    assert args.react_output is None
    assert args.templates_dir == "templates"


def test_emit_markdown(tmp_path: Path, capsys):
    # When an output path is provided the Markdown is persisted and a helper
    # message is emitted.
    destination = tmp_path / "heatmap.md"
    saved_path = cli.emit_markdown("demo", str(destination))

    assert saved_path == destination
    assert destination.read_text(encoding="utf-8") == "demo"

    # Without an output path, the Markdown should be printed to stdout.
    cli.emit_markdown("table", None)
    output = capsys.readouterr().out
    assert "table" in output
