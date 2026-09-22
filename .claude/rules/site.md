---
paths:
  - "**/site/**"
  - "**/blueprints/*/README*.md"
  - "**/blueprints/*/blueprint.toml"
---

# The website

These rules apply when you change the site (`site/`) or any text it shows (a blueprint's `blueprint.toml` or READMEs).

- Always follow front-end best practices
- The website must load fast
- Every text that the site shows exists in pt-BR, en-US and es, and nothing falls back to another language: the interface (`site/i18n.py`), each entry's metadata in `blueprint.toml` (`title`, `summary`, `credits`, `name` and `alt`, with their `[en]`, `[es]`, `name_<lang>` and `alt_<lang>` translations) and each entry's README (`README.md`, `README.en.md` and `README.es.md`, which the entry's page shows as its report). Each language's pages serve their own players, so a page that shows text in another language is a defect. `scripts/catalog/validate.py` and `site/build.py` refuse a missing translation and a translated README whose structure differs from `README.md`, and CI runs them; whether a translation says the same thing only a reader can tell, which is the job of `language-reviewer`
