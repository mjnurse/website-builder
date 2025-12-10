Builder — Simple Python static site generator

Quick start

1. Create or add Markdown content under `content/` organized into directories (directories become sections).
2. Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

3. Build the site (outputs to `site/` by default):

```bash
python3 build.py --src content --out site
```

4. Serve the `site/` directory (e.g., `python3 -m http.server --directory site 8000`).

Project layout

- `build.py` — the builder script.
- `templates/` — Jinja2 templates used to render pages.
- `static/` — CSS and other static assets copied to output.
- `content/` — directory containing Markdown files.
- `site/` — generated output (created by the builder).

Notes

- The builder extracts the first Markdown heading as the page title if present.
- The site navigation is generated from the top-level directories inside `content/`.
