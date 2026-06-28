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


SKILLS = ["api-warehouse", "connect", "assess", "land", "validate", "schedule"]

def _frontmatter(path):
    text = path.read_text()
    assert text.startswith("---"), f"{path} missing frontmatter"
    fm = text.split("---", 2)[1]
    return fm

def test_connect_skill_present_with_frontmatter():
    p = ROOT / "skills" / "connect" / "SKILL.md"
    assert p.exists()
    fm = _frontmatter(p)
    assert "name:" in fm and "description:" in fm

def test_assess_skill_present():
    p = ROOT / "skills" / "assess" / "SKILL.md"
    assert p.exists()
    body = p.read_text()
    assert "endpoints.json" in body
    assert "not API documentation" in body  # input guard wording present

def test_land_skill_present():
    p = ROOT / "skills" / "land" / "SKILL.md"
    assert p.exists()
    body = p.read_text()
    assert "build_rest_api_config" in body
    assert "destinations.md" in body
