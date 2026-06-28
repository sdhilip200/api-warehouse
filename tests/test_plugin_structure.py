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
