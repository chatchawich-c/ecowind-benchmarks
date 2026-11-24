# Grant No. ERASMUS-EDU-2025-CBHE-101177220 (EU Erasmus+ CBHE ECO-WIND)

# Release & Zenodo DOI Guide

This guide explains how to create a GitHub release for **ECO‑WIND Benchmarks** (e.g., `v0.1.0`) and register a corresponding DOI on Zenodo.

---

## 1️⃣ Prepare the release

1. **Update version** – Ensure the `version` field in `CITATION.cff` and the `pyproject.toml` / benchmark scripts reflect the new tag (e.g., `0.1.0`).
2. **Commit & push** – All changes must be merged to the default branch (`main` or `master`).
3. **Create a tag** – From the repository root:
   ```bash
   git tag -a v0.1.0 -m "Release v0.1.0 – initial benchmark suite"
   git push origin v0.1.0
   ```
4. **Open a GitHub release**:
   * Go to **Releases → Draft a new release**.
   * Select the tag `v0.1.0` (GitHub will auto‑populate the title).
   * Write a concise description (changelog, highlights, citation notice).
   * Attach any release assets (e.g., compiled wheels, zip of benchmark results) **only if they respect the ≤ 150 MiB peak‑RSS budget** and follow the zero‑duplication data policy (no raw datasets are bundled).
   * Publish the release.

---

## 2️⃣ Link the release to Zenodo

1. **Enable Zenodo‑GitHub integration** (once per repository):
   * Log in to [Zenodo](https://zenodo.org/) and go to **Account → GitHub**.
   * Authorise the Zenodo app for your GitHub account and enable the **ecowind‑benchmarks** repository.
2. **Create a snapshot**:
   * After the GitHub release is published, Zenodo automatically creates a **new version** (snapshot) for that tag.
   * The Zenodo landing page will show a DOI like `10.5281/zenodo.XXXXXX`. Increment the suffix for each new release.
3. **Add DOI badge** to the repo README (optional):
   ```markdown
   [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXX)
   ```
4. **Update `CITATION.cff`** – replace the placeholder DOI with the Zenodo DOI assigned to the release.

---

## 3️⃣ Attribution & Policy reminders

* **EU Erasmus+ CBHE ECO‑WIND attribution** must appear in all public documents and the `CITATION.cff` abstract (already included).
* **Zero‑duplication data policy** – benchmark scripts generate any required data on‑the‑fly; no external data files are shipped with the release.
* **Memory budget** – all benchmark scripts are designed to stay **≤ 150 MiB** peak RSS; this guarantee should be mentioned in the release notes.

---

## 4️⃣ Verify the release

After publishing, you can check the Zenodo entry:
```bash
curl -s https://zenodo.org/api/records/XXXXXX | jq '.metadata.title, .metadata.doi'
```
The title should match "ECO‑WIND Benchmarks" and the DOI should correspond to the latest GitHub tag.

---

*End of guide.*
