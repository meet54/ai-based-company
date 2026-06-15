"""Repair broken project previews (stub LLM output like <html>...</html>)."""
import asyncio
import sys

from src.database.repository import db, init_db
from src.services.code_generator import code_generator


async def main() -> None:
    await init_db()
    project_ids = [int(x) for x in sys.argv[1:]] if len(sys.argv) > 1 else None
    projects = await db.list_projects()
    if project_ids:
        projects = [p for p in projects if p.id in project_ids]

    for project in projects:
        if not code_generator.has_preview(project.id):
            continue
        try:
            html = code_generator.read_file(project.id, "index.html")
        except FileNotFoundError:
            continue
        files = [{"path": "index.html", "content": html}]
        if not code_generator._is_valid_generation(files):
            result = code_generator.write_premium_site(project)
            print(f"Repaired project {project.id}: {project.title} ({result['file_count']} files)")
        else:
            print(f"OK project {project.id}: {project.title}")


if __name__ == "__main__":
    asyncio.run(main())
