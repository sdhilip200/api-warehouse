import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def test_plugin_manifest_is_valid():
    manifest = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "api-warehouse"
    assert isinstance(manifest.get("skills", []), list)

def test_package_imports():
    import api_warehouse
    assert api_warehouse.__version__


REFERENCES = ["security", "auth-patterns", "pagination-patterns", "incremental-detection", "destinations"]

def test_reference_docs_exist_and_nonempty():
    for ref in REFERENCES:
        p = ROOT / "references" / f"{ref}.md"
        assert p.exists(), f"missing reference: {ref}"
        assert len(p.read_text().strip()) > 200
