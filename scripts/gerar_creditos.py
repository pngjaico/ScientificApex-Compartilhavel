"""Build source-based bilingual acknowledgements without installing dependencies."""
from __future__ import annotations

import importlib.metadata as metadata
import json
from pathlib import Path
import re
import shutil
import tomllib

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "third_party"


def canonical(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def cell(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "not recorded")).replace("|", "\\|")


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def python_packages() -> list[dict]:
    distributions = {canonical(d.metadata["Name"]): d for d in metadata.distributions() if d.metadata["Name"]}
    rows: dict[tuple[str, str], dict] = {}
    for lock in sorted([ROOT / "uv.lock", *(ROOT / "modelos").rglob("uv.lock")]):
        if any(part.startswith(".") for part in lock.relative_to(ROOT).parts):
            continue
        for package in tomllib.loads(lock.read_text(encoding="utf-8"))["package"]:
            if "registry" not in package.get("source", {}):
                continue  # Local applications are not third-party dependencies.
            name, version = package["name"], package["version"]
            key = (canonical(name), version)
            row = rows.setdefault(key, {
                "ecosystem": "Python", "name": name, "version": version,
                "url": f"https://pypi.org/project/{name}/{version}/", "locks": [],
                "author": "Project maintainers and contributors (names not in lock)",
                "license": "NOASSERTION", "license_evidence": "not present in uv.lock",
                "license_files": [],
            })
            row["locks"].append(relative(lock))
            dist = distributions.get(canonical(name))
            if dist is None or dist.version != version:
                continue
            info = dist.metadata
            row["author"] = info.get("Author") or "Project maintainers and contributors"
            expression = info.get("License-Expression")
            raw_license = info.get("License", "")
            classifiers = [c.rsplit(" :: ", 1)[-1] for c in info.get_all("Classifier", []) if c.startswith("License ::")]
            row["license"] = expression or (raw_license.strip() if len(raw_license) < 160 else " / ".join(classifiers)) or "NOASSERTION"
            row["license_evidence"] = f"installed distribution metadata, exact version {version}"
            for item in dist.files or []:
                basename = Path(str(item)).name.upper()
                if not (basename.startswith(("LICENSE", "COPYING", "NOTICE", "AUTHORS")) and ".dist-info/" in str(item).replace("\\", "/")):
                    continue
                source = Path(dist.locate_file(item))
                if not source.is_file() or source.stat().st_size > 2_000_000:
                    continue
                subpath = str(item).replace("\\", "/").split(".dist-info/", 1)[1]
                destination = OUT / "licenses" / "python" / f"{name}-{version}" / subpath
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                target = relative(destination)
                if target not in row["license_files"]:
                    row["license_files"].append(target)
    # Skills can declare additional optional dependencies in PEP 723 headers.
    for script in sorted((ROOT / "skills").rglob("*.py")):
        content = script.read_text(encoding="utf-8-sig")
        for block in re.findall(r"(?ms)^# /// script\r?\n(.*?)^# ///\s*$", content):
            declaration = "\n".join(line[2:] if line.startswith("# ") else line[1:] for line in block.splitlines())
            for requirement in tomllib.loads(declaration).get("dependencies", []):
                match = re.match(r"[a-zA-Z0-9_.-]+", requirement)
                if not match:
                    continue
                name = match.group()
                matches = [row for row in rows.values() if canonical(row["name"]) == canonical(name)]
                if not matches:
                    row = {"ecosystem": "Python", "name": name, "version": "unlocked skill declaration",
                           "url": f"https://pypi.org/project/{name}/", "locks": [],
                           "author": "Project maintainers and contributors", "license": "NOASSERTION",
                           "license_evidence": "optional PEP 723 dependency, not installed or license-verified", "license_files": []}
                    rows[(canonical(name), row["version"])] = row
                    matches = [row]
                for row in matches:
                    item = {"source": relative(script), "requirement": requirement}
                    if item not in row.setdefault("skill_declarations", []):
                        row["skill_declarations"].append(item)
    return sorted(rows.values(), key=lambda row: (row["name"], row["version"]))


def r_packages() -> list[dict]:
    rows: dict[tuple[str, str], dict] = {}
    for lock in sorted((ROOT / "modelos").rglob("renv.lock")):
        for name, package in json.loads(lock.read_text(encoding="utf-8-sig")).get("Packages", {}).items():
            key = (name, package["Version"])
            row = rows.setdefault(key, {
                "ecosystem": "R", "name": name, "version": package["Version"],
                "url": f"https://cran.r-project.org/package={name}",
                "author": package.get("Author") or package.get("Authors@R") or "Package authors and contributors",
                "license": package.get("License", "NOASSERTION"),
                "license_evidence": "renv.lock package metadata (not a legal audit)", "locks": [],
            })
            row["locks"].append(relative(lock))
    return sorted(rows.values(), key=lambda row: (row["name"].lower(), row["version"]))


def npm_packages() -> list[dict]:
    lock = ROOT / "tools/playwright/package-lock.json"
    rows = []
    for path, package in json.loads(lock.read_text(encoding="utf-8"))["packages"].items():
        if not path:
            continue
        name = path.split("node_modules/")[-1]
        rows.append({"ecosystem": "npm", "name": name, "version": package["version"],
                     "url": f"https://www.npmjs.com/package/{name}/v/{package['version']}",
                     "author": "Project maintainers and contributors", "license": package.get("license", "NOASSERTION"),
                     "license_evidence": relative(lock), "locks": [relative(lock)]})
    return rows


def skill_credits() -> list[dict]:
    registry = json.loads((ROOT / "skills/registry.json").read_text(encoding="utf-8"))["skills"]
    rows = []
    for entrypoint in sorted((ROOT / "skills").glob("*/SKILL.md")):
        name = entrypoint.parent.name
        registered = registry.get(name, {})
        parts = entrypoint.read_text(encoding="utf-8-sig").split("---", 2)
        try:
            frontmatter = yaml.safe_load(parts[1]) if len(parts) == 3 else {}
        except yaml.YAMLError:
            frontmatter = {}
        frontmatter = frontmatter if isinstance(frontmatter, dict) else {}
        nested = frontmatter.get("metadata") or {}
        nested = nested if isinstance(nested, dict) else {}
        origin = registered.get("origin", {})
        stated_author = nested.get("skill-author") or frontmatter.get("author")
        declared_license = frontmatter.get("license") or registered.get("license", "NOASSERTION")
        unresolved = origin.get("url", "").startswith("local:") or declared_license in {"NOASSERTION", "LicenseRef-Local-Private"}
        rows.append({"name": name, "path": relative(entrypoint),
                     "author": stated_author or origin.get("provider") or "Origin not established",
                     "url": origin.get("url", ""), "revision": registered.get("pinned_revision", "unverified"),
                     "license": declared_license, "registry_license": registered.get("license", "NOASSERTION"),
                     "license_evidence": "SKILL.md frontmatter / skills/registry.json",
                     "attribution_review_required": unresolved})
    return rows


def write_tables(payload: dict, language: str) -> None:
    pt = language == "portugues"
    title = "Créditos e componentes de terceiros" if pt else "Credits and third-party components"
    intro = (
        "Agradecemos aos autores, mantenedores e comunidades dos projetos abaixo. Esta máquina integra trabalho de terceiros; não reivindica autoria exclusiva dessas contribuições.\n\n"
        "O inventário inclui dependências diretas e transitivas dos locks, ambientes opcionais e skills presentes. Estar no lock não significa ter sido instalado ou executado. A licença Apache-2.0 da camada local não substitui licenças de terceiros. Origem local, NOASSERTION e LicenseRef-Local-Private são pendências, não confirmação de código aberto.\n\n"
        "Metadados de autores e licenças vêm dos arquivos indicados, sem autenticação jurídica. Para citação acadêmica, consulte CITATION/CITATION.cff/citation() de cada ferramenta realmente usada. Créditos não implicam endosso dos mantenedores.\n\n"
        if pt else
        "We thank the authors, maintainers and communities listed below. This machine integrates third-party work and does not claim exclusive authorship of these contributions.\n\n"
        "The inventory includes direct/transitive locked dependencies, optional environments and installed skill trees. A lock entry does not prove installation or execution. The local Apache-2.0 license does not replace upstream terms. Local origins, NOASSERTION and LicenseRef-Local-Private remain unresolved, not confirmed open-source rights.\n\n"
        "Author and license metadata come from the indicated files, without legal authentication. For scholarly citation, consult each actually used tool's CITATION/CITATION.cff/citation(). Acknowledgement does not imply maintainer endorsement.\n\n"
    )
    lines = [f"# {title}\n", intro,
             "[NOTICE](../../NOTICE) · [Third-party notices](../../THIRD_PARTY_NOTICES.md) · [JSON inventory](../../third_party/inventario_creditos.json)\n",
             f"## {'Skills incluídas' if pt else 'Included skills'}\n",
             "| Skill | Authors / source | Revision | License | Evidence | Review |",
             "| --- | --- | --- | --- | --- | --- |"]
    for row in payload["skills"]:
        source = row["url"]
        authors = f"[{cell(row['author'])}]({source})" if source.startswith("https://") else cell(row["author"])
        review = ("Pendente" if pt else "Pending") if row["attribution_review_required"] else "Recorded"
        lines.append(f"| {cell(row['name'])} | {authors} | {cell(row['revision'])} | {cell(row['license'])} | [{row['path']}](../../{row['path']}) | {review} |")
    for ecosystem in ("Python", "R", "npm"):
        lines.extend([f"\n## {ecosystem}\n", "| Component | Version | Authors / maintainers | License metadata | Source files |",
                      "| --- | --- | --- | --- | --- |"])
        for row in payload["packages"]:
            if row["ecosystem"] != ecosystem:
                continue
            sources = row["locks"] or sorted({item["source"] for item in row.get("skill_declarations", [])})
            locks = ", ".join(f"[{path}](../../{path})" for path in sources)
            lines.append(f"| [{cell(row['name'])}]({row['url']}) | {cell(row['version'])} | {cell(row['author'])} | {cell(row['license'])} | {locks} |")
    destination = ROOT / "docs" / language / "creditos_opensource.md"
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    payload = {"contract": "ThirdPartyAttributionInventoryV1", "evidence_date": "2026-11-06",
               "scope": "Distributed skills, all included uv/renv/npm locks, optional PEP 723 declarations, exact-version installed Python metadata",
               "skills": skill_credits(), "packages": python_packages() + r_packages() + npm_packages()}
    (OUT / "inventario_creditos.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for language in ("portugues", "ingles"):
        write_tables(payload, language)
    for kind in ("Python", "R", "npm"):
        print(f"{kind}: {sum(row['ecosystem'] == kind for row in payload['packages'])} package/version entries")
    print(f"Skills: {len(payload['skills'])}; attribution/license review pending: {sum(row['attribution_review_required'] for row in payload['skills'])}")
    print(f"License/notice text files: {sum(path.is_file() for path in (OUT / 'licenses').rglob('*'))}")


if __name__ == "__main__":
    main()
