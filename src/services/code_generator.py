import json
import re
from pathlib import Path

from src.config import settings
from src.models.schemas import Project
from src.services.llm import llm_service
from src.services.website_templates import build_premium_site

ROOT = Path(__file__).resolve().parent.parent.parent
DELIVERABLES_DIR = ROOT / "deliverables"


class CodeGenerator:
    def list_files(self, project_id: int) -> list[dict]:
        base = self.project_dir(project_id)
        if not base.exists():
            return []
        files = []
        for path in sorted(base.rglob("*")):
            if path.is_file():
                rel = path.relative_to(base).as_posix()
                files.append({
                    "path": rel,
                    "size": path.stat().st_size,
                    "extension": path.suffix.lstrip("."),
                })
        return files

    def project_dir(self, project_id: int) -> Path:
        return DELIVERABLES_DIR / f"project-{project_id}"

    def has_preview(self, project_id: int) -> bool:
        return (self.project_dir(project_id) / "index.html").is_file()

    def preview_url(self, project_id: int) -> str | None:
        if self.has_preview(project_id):
            return f"/deliverables/{project_id}/index.html"
        return None

    def read_file(self, project_id: int, file_path: str) -> str:
        base = self.project_dir(project_id).resolve()
        target = (base / file_path).resolve()
        if not str(target).startswith(str(base)):
            raise ValueError("Invalid file path")
        if not target.is_file():
            raise FileNotFoundError(file_path)
        return target.read_text(encoding="utf-8", errors="replace")

    async def generate(self, project: Project) -> dict:
        DELIVERABLES_DIR.mkdir(parents=True, exist_ok=True)
        out_dir = self.project_dir(project.id)
        if out_dir.exists():
            for f in out_dir.rglob("*"):
                if f.is_file():
                    f.unlink()
        out_dir.mkdir(parents=True, exist_ok=True)

        prompt = self._build_prompt(project)
        system = (
            "You are an elite frontend developer at a top IT agency. "
            "Build a STUNNING, production-quality website that fulfills ALL client requirements.\n"
            "Return ONLY valid JSON: {\"files\": [{\"path\": \"relative/path.ext\", \"content\": \"...\"}]}\n\n"
            "MANDATORY QUALITY STANDARDS:\n"
            "- Premium dark/light modern design (like Stripe, Linear, Vercel quality)\n"
            "- Google Fonts (Inter + display font), CSS variables, gradients, glass effects\n"
            "- Hero section, features from requirements, about, contact form, footer\n"
            "- Fully responsive mobile-first CSS\n"
            "- Implement EVERY requirement the client listed — no generic placeholder text\n"
            "- Real content based on client industry and project description\n"
            "- Smooth hover effects and professional spacing\n"
            "- Files: index.html, styles.css, app.js, README.md (min 4 files)\n"
            "- No markdown fences — raw JSON only\n"
            "- Escape newlines in JSON strings properly"
        )

        raw = await llm_service.complete(system, prompt)
        files = self._parse_files(raw, project)
        if not self._is_valid_generation(files):
            files = build_premium_site(
                title=project.title,
                client=project.client_name,
                company=settings.company_name,
                description=project.description,
                requirements=project.requirements or project.description,
            )

        written = []
        for item in files:
            rel_path = item["path"].replace("\\", "/").lstrip("/")
            if ".." in rel_path:
                continue
            dest = out_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(item["content"], encoding="utf-8")
            written.append(rel_path)

        return {
            "directory": str(out_dir.relative_to(ROOT)),
            "files_written": written,
            "file_count": len(written),
        }

    def _build_prompt(self, project: Project) -> str:
        parts = [
            f"Project: {project.title}",
            f"Client: {project.client_name} ({project.client_company})",
            f"Description: {project.description}",
        ]
        if project.requirements:
            parts.append(f"Requirements:\n{project.requirements[:3000]}")
        if project.tech_stack:
            parts.append(f"Tech Stack:\n{project.tech_stack[:1000]}")
        parts.append(
            "CRITICAL: The website MUST look premium and professional — not basic or ugly. "
            "Every requirement above must appear as a real section or feature on the site. "
            "Use a cohesive color scheme matching the client's industry."
        )
        return "\n\n".join(parts)

    def _is_valid_generation(self, files: list[dict]) -> bool:
        if not files:
            return False
        by_path: dict[str, str] = {}
        for item in files:
            path = item.get("path", "").replace("\\", "/").lstrip("/")
            by_path[path] = item.get("content", "")

        html = by_path.get("index.html", "")
        if len(html) < 400:
            return False
        if re.search(r"<html>\s*\.\.\.\s*</html>", html, re.I):
            return False
        if html.count("...") >= 2 and len(html) < 800:
            return False
        if not re.search(r"<(?:!doctype|body|main|section|header|nav)\b", html, re.I):
            return False

        css = by_path.get("styles.css", "")
        if css and len(css) < 120:
            return False
        if re.fullmatch(r"/\*\s*\.\.\.\s*\*/", css.strip()):
            return False
        return True

    def _parse_files(self, raw: str, project: Project) -> list[dict]:
        try:
            match = re.search(r"\{[\s\S]*\}", raw)
            if match:
                data = json.loads(match.group())
                files = data.get("files", [])
                if files and all("path" in f and "content" in f for f in files):
                    if self._is_valid_generation(files):
                        return files
        except (json.JSONDecodeError, KeyError):
            pass
        return build_premium_site(
            title=project.title,
            client=project.client_name,
            company=settings.company_name,
            description=project.description,
            requirements=project.requirements or project.description,
        )


    def write_premium_site(self, project: Project) -> dict:
        """Write premium template files for an existing project (repair bad generations)."""
        files = build_premium_site(
            title=project.title,
            client=project.client_name,
            company=settings.company_name,
            description=project.description,
            requirements=project.requirements or project.description,
        )
        out_dir = self.project_dir(project.id)
        out_dir.mkdir(parents=True, exist_ok=True)
        written = []
        for item in files:
            rel_path = item["path"].replace("\\", "/").lstrip("/")
            dest = out_dir / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(item["content"], encoding="utf-8")
            written.append(rel_path)
        return {
            "directory": str(out_dir.relative_to(ROOT)),
            "files_written": written,
            "file_count": len(written),
        }


code_generator = CodeGenerator()
