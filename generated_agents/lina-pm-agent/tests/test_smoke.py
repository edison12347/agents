from pathlib import Path

def test_generated_layout():
    root = Path(__file__).resolve().parents[1]
    assert (root / 'config' / 'openclaw.json').exists()
    assert (root / 'workspace' / 'AGENTS.md').exists()
    assert (root / 'README.md').read_text().startswith('# lina-pm-agent')
