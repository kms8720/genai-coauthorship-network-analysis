# Generative AI Research Ecosystem

Competition and Collaboration in Firm-University Coauthorship Networks

## Research Question

Is the generative AI research ecosystem organized as a closed firm-centered competitive structure, or as a mixed/collaborative structure connected through universities, research institutions, and mobile researchers?

## Data Source

This project uses the OpenAlex Works API to collect papers from 2022 to 2025 matching generative AI search terms. OpenAlex currently documents API access as free but requiring a free API key. The collector can be configured to write a tiny offline validation sample when the API is unavailable, but the submitted outputs use real OpenAlex records rather than the offline sample. See the OpenAlex authentication and pricing documentation: https://developers.openalex.org/

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
python scripts/07_make_report_ready_figures.py
```

## Output Folders

- `data/raw/`: raw OpenAlex JSONL and collection metadata. Large raw files are ignored by Git.
- `data/processed/`: cleaned works, authorships, institutions, and author-year affiliations.
- `outputs/networks/`: node and edge CSV files for researcher and institution networks.
- `outputs/gephi/`: GEXF files for Gephi.
- `outputs/tables/`: centrality, mixing, bridge, and network summary tables.
- `outputs/figures/`: PNG/PDF visualizations, including filtered report-ready network figures.
- `outputs/report/`: summary report and GitHub upload checklist.

## Limited Run vs Full Run

`config.yaml` defaults to a limited collection run:

- `full_run: false`
- `max_pages_per_query: 5`
- `per_page: 100`

For real data collection, set `OPENALEX_API_KEY` first. For a larger collection, set `full_run: true` or increase `max_pages_per_query`.

## Affiliation Framework

The pipeline uses OpenAlex author IDs as researcher node IDs, but it does not rely on one all-period modal institution as the analytical affiliation. It builds an authorship-level affiliation table and an author-year affiliation table. Yearly researcher networks use same-year affiliations, while the full-period network stores latest, dominant, and all observed affiliations from 2022 to 2025.

Conservative raw-affiliation rules recover clearly named target AI firms when OpenAlex has raw strings but no structured institution record. This matters for cases such as Anthropic, where the raw affiliation can be present even when OpenAlex does not attach a structured institution ID.

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
- `outputs/tables/authorship_affiliations_long.csv`
- `outputs/tables/author_year_affiliations.csv`
- `outputs/tables/researcher_affiliation_changes.csv`
- `outputs/tables/edge_type_mixing.csv`
- `outputs/tables/top_researchers_betweenness.csv`
- `outputs/tables/potential_bridge_researchers.csv`
- `outputs/tables/potential_bridge_institutions.csv`
- `outputs/figures/report_institution_backbone.png`
- `outputs/figures/report_company_academic_subnetwork.png`
- `outputs/figures/report_bridge_institution_ego_network.png`
- `outputs/figures/report_bridge_researcher_ego_network.png`
- `outputs/figures/report_institution_community_network.png`
- `outputs/report/summary_report.md`
- `outputs/report/github_upload_checklist.md`

Note: `outputs/gephi/researcher_full.gexf` is generated locally but excluded from Git because the full researcher graph can exceed GitHub's 100 MB single-file limit. Recreate it by rerunning `python scripts/03_build_networks.py` after collecting data.

## Reproducibility Notes

The project records raw OpenAlex responses before cleaning. The current submitted outputs are based on 16,000 processed OpenAlex works from a limited real-data collection run. Offline validation samples, if explicitly enabled in `config.yaml`, should not be used for substantive conclusions. OpenAlex metadata can change over time, so rerunning later may produce slightly different counts.
