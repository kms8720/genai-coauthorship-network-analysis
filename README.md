# Generative AI Research Ecosystem

Competition and Collaboration in Firm-University Coauthorship Networks

## Research Question

Is the generative AI research ecosystem organized as a closed firm-centered competitive structure, or as a mixed/collaborative structure connected through universities, research institutions, and mobile researchers?

## Data Source

This project uses the OpenAlex Works API to collect papers from 2022 to 2025 matching generative AI search terms. OpenAlex currently documents API access as free but requiring a free API key. If no key is available or the API is rate-limited, the collector can write a tiny offline validation sample so the rest of the pipeline can still be tested. See the OpenAlex authentication and pricing documentation: https://developers.openalex.org/

## Install Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Optional Environment Variables

Do not hardcode credentials in scripts. Put the API key in your shell environment:

```bash
export OPENALEX_API_KEY="your_openalex_api_key"
export OPENALEX_EMAIL="your_email@example.com"
```

## Run the Full Pipeline

```bash
python scripts/01_collect_openalex.py
python scripts/02_clean_and_build_tables.py
python scripts/03_build_networks.py
python scripts/04_analyze_networks.py
python scripts/05_visualize_networks.py
python scripts/06_make_summary_report.py
```

## Output Folders

- `data/raw/`: raw OpenAlex JSONL and collection metadata. Large raw files are ignored by Git.
- `data/processed/`: cleaned works, authorships, institutions, and author-year affiliations.
- `outputs/networks/`: node and edge CSV files for researcher and institution networks.
- `outputs/gephi/`: GEXF files for Gephi.
- `outputs/tables/`: centrality, mixing, bridge, and network summary tables.
- `outputs/figures/`: PNG visualizations.
- `outputs/report/`: summary report and GitHub upload checklist.

## Sample Mode vs Full Mode

`config.yaml` defaults to sample/test mode:

- `full_run: false`
- `max_pages_per_query: 5`
- `per_page: 100`

For real data collection, set `OPENALEX_API_KEY` first. For a larger collection, set `full_run: true` or increase `max_pages_per_query`.

## Open GEXF Files in Gephi

Open Gephi, choose **File > Open**, then select files such as:

- `outputs/gephi/researcher_full.gexf`
- `outputs/gephi/institution_full.gexf`
- `outputs/gephi/institution_2025.gexf`

Use node color fields such as `simplified_institution_category`, `target_firm_label`, or `community`.

## Main Generated Outputs

- `data/processed/works.csv`
- `data/processed/authorships.csv`
- `data/processed/institutions.csv`
- `outputs/tables/network_summary_by_year.csv`
- `outputs/tables/top_researchers_betweenness.csv`
- `outputs/tables/potential_bridge_researchers.csv`
- `outputs/tables/potential_bridge_institutions.csv`
- `outputs/report/summary_report.md`
- `outputs/report/github_upload_checklist.md`

Note: `outputs/gephi/researcher_full.gexf` is generated locally but excluded from Git because the full researcher graph can exceed GitHub's 100 MB single-file limit. Recreate it by rerunning `python scripts/03_build_networks.py` after collecting data.

## Reproducibility Notes

The project records raw OpenAlex responses before cleaning. The default run is intentionally small to avoid high API cost and long runtime. If the API key is missing or rate-limited, the scripts may generate a small offline validation dataset; do not use that sample for substantive conclusions. OpenAlex metadata can change over time, so rerunning later may produce slightly different counts.
