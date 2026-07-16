# Changelog

All notable changes to **EarningsIQ** will be documented in this file. The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-07-15
### Added
* **Premium Light-Mode Glassmorphism**: Complete CSS overrides for responsive HSL white backdrops, soft shadows, and light cyan/indigo container accents.
* **Typewriter Header Animation**: Keyframe terminal text animation typing out "EarningsIQ" on app load.
* **Pulsing Agent Status Indicators**: Visual status lights denoting live active multi-agent cycles.
* **GitHub CI Actions Workflow**: Automated pipeline configuration running `pytest` test suites on commits.
* **Dynamic Git Commit Footer tracker**: Automated SHA fetch displayed alongside repository status badges.
* **Startup Data Sweeper**: Automated directory sweep to purge user-uploaded files on session reset.
* **BM25 Empty Corpus Fallback**: Automatic vector scoring weight re-balance when BM25 fails.
* **Context Truncation**: Safety token buffer cap truncating retrieved paragraphs to 40,000 characters.

### Fixed
* **LaTeX Delimiter Collision**: Escaped dollar signs (`\$`) to prevent Streamlit markdown math formatting errors.
* **Math Verifier zero divisor logic**: Divisor zeros verified as arithmetic errors rather than silently passing.
* **Math Ratios Tolerance**: Added a 5% relative difference check for leverage and multiple ratios > 1.0.
* **Slide text duplicates filter**: Filtered out consecutive repeated line layout copies.
* **ChromaDB SQLite version bypass**: Added `pysqlite3-binary` and swap override block to support Streamlit Cloud.
* **Test target paths**: Swapped missing test PDFs for successfully downloaded `real_tsla_deck.pdf` references.

---

## [1.0.0] - 2026-07-14
### Added
* **Fast Mode Pipeline**: Direct synthesis querying RAG in a single LLM request alongside concurrent auditor execution.
* **Streamlit cloud hot-reload cache handler**: TypeError fallback block preventing module mismatch crashes.
* **Markdown Playground**: Formatted markdown rendering for qualitative logs and internal agent draft iterations.
* **Grounding & Arithmetic separations**: Dedicated audit panels separating numerical recalculations and citations.
