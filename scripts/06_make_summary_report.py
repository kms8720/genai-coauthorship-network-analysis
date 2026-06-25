from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from common import DATA_PROCESSED, DATA_RAW, OUTPUTS, PROJECT_ROOT, ensure_dirs, env_note


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() and path.stat().st_size > 0 else pd.DataFrame()


def md_table(df: pd.DataFrame, cols=None, n: int = 10) -> str:
    if df.empty:
        return "No rows generated."
    if cols:
        cols = [c for c in cols if c in df.columns]
        df = df[cols]
    df = df.head(n).fillna("")
    headers = [str(c) for c in df.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for _, row in df.iterrows():
        values = [str(row[c]).replace("|", "/") for c in df.columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def count_files() -> int:
    return sum(1 for p in OUTPUTS.rglob("*") if p.is_file())


def make_report() -> None:
    ensure_dirs()
    works = read_csv(DATA_PROCESSED / "works.csv")
    authorships = read_csv(DATA_PROCESSED / "authorships.csv")
    institutions = read_csv(DATA_PROCESSED / "institutions.csv")
    summary = read_csv(OUTPUTS / "tables" / "network_summary_by_year.csv")
    top_degree = read_csv(OUTPUTS / "tables" / "top_researchers_degree.csv")
    top_between = read_csv(OUTPUTS / "tables" / "top_researchers_betweenness.csv")
    top_eigen = read_csv(OUTPUTS / "tables" / "top_researchers_eigenvector.csv")
    top_inst_between = read_csv(OUTPUTS / "tables" / "top_institutions_betweenness.csv")
    mixing = read_csv(OUTPUTS / "tables" / "institution_type_edge_mixing.csv")
    methods = read_csv(OUTPUTS / "tables" / "centrality_method_summary.csv")
    author_year = read_csv(OUTPUTS / "tables" / "author_year_affiliations.csv")
    long_affils = read_csv(OUTPUTS / "tables" / "authorship_affiliations_long.csv")
    mobility = read_csv(OUTPUTS / "tables" / "researcher_affiliation_changes.csv")
    edge_mixing = read_csv(OUTPUTS / "tables" / "edge_type_mixing.csv")
    cleaning_summary = {}
    summary_path = DATA_PROCESSED / "cleaning_summary.json"
    if summary_path.exists():
        cleaning_summary = json.loads(summary_path.read_text(encoding="utf-8"))

    works_by_year = works["publication_year"].value_counts().sort_index().to_dict() if not works.empty else {}
    full_researcher = summary[(summary["network"] == "researcher") & (summary["year"].astype(str) == "full")]
    full_institution = summary[(summary["network"] == "institution") & (summary["year"].astype(str) == "full")]

    no_observed = cleaning_summary.get("authors_with_no_observed_institution_metadata", "n/a")
    raw_recovered = cleaning_summary.get("authors_with_raw_affiliation_recovered", "n/a")
    multi_affils = cleaning_summary.get("authors_with_multiple_affiliations", "n/a")
    category_changes = cleaning_summary.get("authors_with_category_changes_across_years", "n/a")

    report = f"""# Generative AI Research Ecosystem: Competition and Collaboration in Firm-University Coauthorship Networks

## Research Question

Is the generative AI research ecosystem organized as a closed firm-centered competitive structure, or as a mixed/collaborative structure connected through universities, research institutions, and mobile researchers?

## Data Collection Summary

- Source: OpenAlex Works API
- Environment variables: `{env_note()}`
- Raw file: `data/raw/openalex_works_raw.jsonl`
- Processed works: {len(works)}
- Unique authors: {authorships['author_id'].nunique() if not authorships.empty else 0}
- Unique institutions, including conservative raw-affiliation recoveries: {institutions['institution_id'].nunique() if not institutions.empty else 0}
- Works by year: `{json.dumps(works_by_year, ensure_ascii=False)}`

Limitations: this limited collection run depends on keyword search terms and OpenAlex affiliation metadata. Search terms may miss relevant papers that do not use the selected terminology.

Author IDs are complete in the processed researcher table, but affiliation metadata is incomplete in OpenAlex. Some authors have structured OpenAlex institutions, some only have raw affiliation strings, and some have no observed institution metadata. Because researcher mobility and multi-affiliation are central to this project, the pipeline no longer uses one all-period modal institution as the main analytical affiliation. It now uses an author-year affiliation framework and keeps all observed affiliations for analysis.

Affiliation metadata summary:

- Authors with no observed institution metadata: {no_observed}
- Authors with raw affiliation recovered by conservative rules: {raw_recovered}
- Authors with multiple affiliations in at least one observed year: {multi_affils}
- Authors with primary category changes across years: {category_changes}
- Authorship-level affiliation rows: {len(long_affils)}
- Author-year affiliation rows: {len(author_year)}
- Researcher year-to-year mobility/change rows: {len(mobility)}

Raw affiliation recovery is intentionally conservative and focuses on clearly named target AI firms such as OpenAI, Anthropic, Google DeepMind, Microsoft, NVIDIA, Cohere, Mistral AI, xAI, Stability AI, and Hugging Face.

Betweenness centrality uses exact calculation when network size is feasible and sampling approximation only when node counts exceed `max_exact_betweenness_nodes` in `config.yaml`. Degree, weighted degree, and eigenvector centrality are calculated directly. Community labels use Louvain when available.

Centrality method summary:

{md_table(methods, ['network', 'year', 'node_count', 'edge_count', 'betweenness_method', 'betweenness_k'], 20)}

## Researcher Network Summary

Full network:

{md_table(full_researcher)}

Year-by-year:

{md_table(summary[summary['network'] == 'researcher'] if not summary.empty else summary)}

## Institution Network Summary

Full network:

{md_table(full_institution)}

Year-by-year:

{md_table(summary[summary['network'] == 'institution'] if not summary.empty else summary)}

## Centrality Results

Top degree researchers:

{md_table(top_degree, ['display_name', 'author_id', 'main_institution_name', 'degree_centrality', 'weighted_degree'], 10)}

Top betweenness researchers:

{md_table(top_between, ['display_name', 'author_id', 'main_institution_name', 'betweenness_centrality', 'weighted_degree'], 10)}

Top eigenvector researchers:

{md_table(top_eigen, ['display_name', 'author_id', 'main_institution_name', 'eigenvector_centrality', 'weighted_degree'], 10)}

Top bridge institutions:

{md_table(top_inst_between, ['institution_name', 'institution_id', 'simplified_institution_category', 'target_firm_label', 'betweenness_centrality', 'weighted_degree'], 10)}

## Institution Type Mixing

{md_table(mixing[mixing['year'].astype(str) == 'full'] if not mixing.empty else mixing, ['category_pair', 'edge_count', 'edge_weight'], 20)}

Additional edge mixing methods:

{md_table(edge_mixing[edge_mixing['year'].astype(str) == 'full'] if not edge_mixing.empty else edge_mixing, ['method', 'category_pair', 'edge_count', 'edge_weight'], 30)}

## Evidence Related to Hypotheses

- H1. Partial firm-centered clustering: inspect `target_firm_label`, community labels, and institution network figures. A supported claim requires visible firm-centered communities plus cross-community links.
- H2. Limited direct firm-to-firm collaboration: inspect `outputs/tables/firm_to_firm_edges.csv`.
- H3. Universities and research institutions as bridges: inspect `outputs/tables/potential_bridge_institutions.csv` and company-education rows in `institution_type_edge_mixing.csv`.
- H4. Degree and betweenness may differ: compare `top_researchers_degree.csv` and `top_researchers_betweenness.csv`.
- H5. Increasing connectedness over time: compare density, component count, and largest-component share in `network_summary_by_year.csv`.

## What To Inspect Manually Next

- Top bridge researchers' career histories and affiliation changes.
- Whether bridge roles come from researcher mobility, joint appointments, or large multi-institution papers.
- Compare `outputs/tables/author_year_affiliations.csv` and `outputs/tables/researcher_affiliation_changes.csv` before making claims about mobility.
- Institution classification rules in `institution_classification_rules.md`, especially ambiguous organizations.
- Papers with large author lists that were excluded from pairwise researcher edges by the configurable threshold.

## Files Generated

- Processed tables: `data/processed/`
- Network tables: `outputs/networks/`
- Gephi files: `outputs/gephi/`
- Metric tables: `outputs/tables/`
- Authorship affiliation long table: `outputs/tables/authorship_affiliations_long.csv`
- Author-year affiliation table: `outputs/tables/author_year_affiliations.csv`
- Researcher affiliation changes: `outputs/tables/researcher_affiliation_changes.csv`
- Edge mixing methods: `outputs/tables/edge_type_mixing.csv`
- Figures: `outputs/figures/`
- This report: `outputs/report/summary_report.md`
- GitHub checklist: `outputs/report/github_upload_checklist.md`

## Next-Step Instructions

For a larger run, edit `config.yaml`: set `full_run: true` or increase `max_pages_per_query`. Set `OPENALEX_API_KEY` for a larger daily allowance and optionally set `OPENALEX_EMAIL`.

Then rerun:

```bash
python scripts/01_collect_openalex.py
python scripts/02_clean_and_build_tables.py
python scripts/03_build_networks.py
python scripts/04_analyze_networks.py
python scripts/05_visualize_networks.py
python scripts/06_make_summary_report.py
```
"""
    (OUTPUTS / "report" / "summary_report.md").write_text(report, encoding="utf-8")

    checklist = """# GitHub Upload Checklist

## Commit These Files

- `README.md`
- `requirements.txt`
- `config.yaml`
- `institution_classification_rules.md`
- `scripts/`
- `data/processed/`
- `outputs/tables/`
- `outputs/networks/`
- `outputs/gephi/`
- `outputs/figures/`
- `outputs/report/`

## Do Not Commit

- `.env`
- API keys or private credentials
- Very large raw files such as `data/raw/openalex_works_raw.jsonl`
- Very large generated graph files such as `outputs/gephi/researcher_full.gexf`
- Python cache files and virtual environments

## Suggested Repository

- Repository name: `genai-coauthorship-network-analysis`
- Existing target URL: `https://github.com/kms8720/genai-coauthorship-network-analysis.git`

## Suggested Commit Message

`Initial generative AI coauthorship network analysis pipeline`

## Exact Git Commands

From the project root:

```bash
git init
git add .
git commit -m "Initial generative AI coauthorship network analysis pipeline"
git branch -M main
git remote add origin https://github.com/kms8720/genai-coauthorship-network-analysis.git
git push -u origin main
```

If GitHub CLI is installed and authenticated:

```bash
gh repo create genai-coauthorship-network-analysis --public --source=. --remote=origin --push
```

Do not push automatically unless the user explicitly requests upload.
"""
    (OUTPUTS / "report" / "github_upload_checklist.md").write_text(checklist, encoding="utf-8")
    print(f"Wrote report to {OUTPUTS / 'report' / 'summary_report.md'}")
    print(f"Generated output files: {count_files()}")


if __name__ == "__main__":
    make_report()
