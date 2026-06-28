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


REFERENCES = ["security", "auth-patterns", "pagination-patterns", "incremental-detection", "destinations", "running-evals", "anti-slop"]

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

def test_validate_skill_present():
    p = ROOT / "skills" / "validate" / "SKILL.md"
    assert p.exists()
    body = p.read_text()
    assert "render_validation" in body
    assert "skipped" in body  # honesty about unavailable checks

def test_dockerignore_excludes_secrets():
    di = (ROOT / "templates" / ".dockerignore").read_text()
    assert ".dlt/secrets.toml" in di
    assert ".env" in di

def test_schedule_skill_and_templates_present():
    assert (ROOT / "skills" / "schedule" / "SKILL.md").exists()
    df = (ROOT / "templates" / "Dockerfile").read_text()
    assert "python" in df.lower()
    for plat in ["cloud-run", "azure-container-apps", "aws-ecs"]:
        assert (ROOT / "templates" / "deploy" / f"{plat}.md").exists()

def test_orchestrator_lists_full_loop():
    body = (ROOT / "skills" / "api-warehouse" / "SKILL.md").read_text()
    for step in ["connect", "assess", "land", "validate", "schedule"]:
        assert step in body
    assert "checkpoint" in body.lower()

def test_all_skills_have_unique_names():
    import re
    names = []
    for s in SKILLS:
        fm = _frontmatter(ROOT / "skills" / s / "SKILL.md")
        m = re.search(r"name:\s*(\S+)", fm)
        names.append(m.group(1))
    assert len(names) == len(set(names))

def test_every_skill_has_evals_and_memory():
    for s in SKILLS:
        evals = ROOT / "skills" / s / "EVALS.md"
        memory = ROOT / "skills" / s / "MEMORY.md"
        assert evals.exists(), f"{s} missing EVALS.md"
        assert memory.exists(), f"{s} missing MEMORY.md"
        assert len(evals.read_text().strip()) > 100, f"{s} EVALS.md too thin"

def test_skills_wire_the_eval_loop():
    for s in SKILLS:
        body = (ROOT / "skills" / s / "SKILL.md").read_text()
        assert "running-evals.md" in body, f"{s} does not link the eval loop"
        assert "EVALS.md" in body, f"{s} does not reference its EVALS.md"

def test_readme_has_install_and_positioning():
    r = (ROOT / "README.md").read_text()
    assert "/plugin marketplace add https://github.com/sdhilip200/api-warehouse" in r
    assert "dlt" in r and "printing-press" in r  # honest positioning section
    assert (ROOT / "CONTRIBUTING.md").exists()
    assert (ROOT / ".github" / "workflows" / "ci.yml").exists()

def test_marketplace_manifest_valid():
    m = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    assert m["name"] == "api-warehouse"
    plugins = m["plugins"]
    assert any(p["name"] == "api-warehouse" and p["source"] == "./" for p in plugins)

def test_codex_plugin_manifest_valid():
    m = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text())
    assert m["name"] == "api-warehouse"
    assert m["skills"] == "./skills/"

def test_agents_md_present_and_lists_skills():
    body = (ROOT / "AGENTS.md").read_text()
    for s in ["connect", "assess", "land", "validate", "schedule"]:
        assert s in body, f"AGENTS.md does not mention {s}"
    assert "Codex" in body
