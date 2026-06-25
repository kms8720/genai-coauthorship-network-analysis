# Generative AI Research Ecosystem: Competition and Collaboration in Firm-University Coauthorship Networks

## Research Question

Is the generative AI research ecosystem organized as a closed firm-centered competitive structure, or as a mixed/collaborative structure connected through universities, research institutions, and mobile researchers?

## Data Collection Summary

- Source: OpenAlex Works API
- Environment variables: `OPENALEX_API_KEY=not set; OPENALEX_EMAIL=not set`
- Raw file: `data/raw/openalex_works_raw.jsonl`
- Processed works: 16000
- Unique authors: 64934
- Unique institutions, including conservative raw-affiliation recoveries: 7425
- Works by year: `{"2022": 3524, "2023": 4040, "2024": 4219, "2025": 4217}`

Limitations: this limited collection run depends on keyword search terms and OpenAlex affiliation metadata. Search terms may miss relevant papers that do not use the selected terminology.

Author IDs are complete in the processed researcher table, but affiliation metadata is incomplete in OpenAlex. Some authors have structured OpenAlex institutions, some only have raw affiliation strings, and some have no observed institution metadata. Because researcher mobility and multi-affiliation are central to this project, the pipeline no longer uses one all-period modal institution as the main analytical affiliation. It now uses an author-year affiliation framework and keeps all observed affiliations for analysis.

Affiliation metadata summary:

- Authors with no observed institution metadata: 14888
- Authors with raw affiliation recovered by conservative rules: 436
- Authors with multiple affiliations in at least one observed year: 12966
- Authors with primary category changes across years: 4700
- Authorship-level affiliation rows: 84940
- Author-year affiliation rows: 77433
- Researcher year-to-year mobility/change rows: 12499

Display affiliation diagnostics:

- Total researcher nodes: 64934
- Authors with blank latest institution display: 14888
- Authors with non-empty dominant display but blank latest display: 0
- Authors whose latest display affiliation has unknown category: 339
- Authors whose most recent observed year has missing affiliation metadata: 15853
- Authors recovered through raw affiliation rules: 436

Display affiliation uses the most recent observed non-empty institution name. If an institution name is available but its category is unknown, the institution name is preserved and only the category remains unknown. This avoids unnecessarily dropping useful affiliation information due to incomplete OpenAlex institution-type metadata.

Raw affiliation recovery is intentionally conservative and focuses on clearly named target AI firms such as OpenAI, Anthropic, Google DeepMind, Microsoft, NVIDIA, Cohere, Mistral AI, xAI, Stability AI, and Hugging Face.

Betweenness centrality uses exact calculation when network size is feasible and sampling approximation only when node counts exceed `max_exact_betweenness_nodes` in `config.yaml`. Degree, weighted degree, and eigenvector centrality are calculated directly. Community labels use Louvain when available.

Centrality method summary:

| network | year | node_count | edge_count | betweenness_method | betweenness_k |
| --- | --- | --- | --- | --- | --- |
| researcher | full | 64934 | 312015 | approximate_weighted_brandes_sampling | 300 |
| institution | full | 7425 | 71650 | exact_weighted_igraph | 0 |
| researcher | 2022 | 16777 | 66924 | approximate_weighted_brandes_sampling | 300 |
| institution | 2022 | 3226 | 24464 | exact_weighted_igraph | 0 |
| researcher | 2023 | 17455 | 85562 | approximate_weighted_brandes_sampling | 300 |
| institution | 2023 | 2609 | 15091 | exact_weighted_igraph | 0 |
| researcher | 2024 | 21419 | 96424 | approximate_weighted_brandes_sampling | 300 |
| institution | 2024 | 2951 | 15038 | exact_weighted_igraph | 0 |
| researcher | 2025 | 21782 | 89296 | approximate_weighted_brandes_sampling | 300 |
| institution | 2025 | 3825 | 25038 | exact_weighted_igraph | 0 |

## Researcher Network Summary

Full network:

| network | year | node_count | edge_count | density | average_degree | connected_components | largest_component_size | share_nodes_largest_component |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| researcher | full | 64934 | 312015 | 0.0001480020884234 | 9.610219607601564 | 9152 | 32305 | 0.4975051590846089 |

Year-by-year:

| network | year | node_count | edge_count | density | average_degree | connected_components | largest_component_size | share_nodes_largest_component |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| researcher | full | 64934 | 312015 | 0.0001480020884234 | 9.610219607601564 | 9152 | 32305 | 0.4975051590846089 |
| researcher | 2022 | 16777 | 66924 | 0.0004755642112733 | 7.978065208320915 | 3733 | 3327 | 0.1983072062943315 |
| researcher | 2023 | 17455 | 85562 | 0.0005616892323454 | 9.803723861357778 | 2253 | 7700 | 0.4411343454597536 |
| researcher | 2024 | 21419 | 96424 | 0.0004203751488968 | 9.003594939072785 | 2930 | 7676 | 0.3583734067883655 |
| researcher | 2025 | 21782 | 89296 | 0.0003764319106966 | 8.199063446882747 | 3607 | 4588 | 0.2106326324488109 |

## Institution Network Summary

Full network:

| network | year | node_count | edge_count | density | average_degree | connected_components | largest_component_size | share_nodes_largest_component |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| institution | full | 7425 | 71650 | 0.002599631371183 | 19.2996632996633 | 548 | 6692 | 0.9012794612794612 |

Year-by-year:

| network | year | node_count | edge_count | density | average_degree | connected_components | largest_component_size | share_nodes_largest_component |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| institution | full | 7425 | 71650 | 0.002599631371183 | 19.2996632996633 | 548 | 6692 | 0.9012794612794612 |
| institution | 2022 | 3226 | 24464 | 0.0047028744166822 | 15.166769993800372 | 360 | 2683 | 0.8316800991940484 |
| institution | 2023 | 2609 | 15091 | 0.0044357427216313 | 11.568417018014564 | 347 | 2070 | 0.7934074357991567 |
| institution | 2024 | 2951 | 15038 | 0.00345484725086 | 10.191799390037277 | 329 | 2426 | 0.8220942053541173 |
| institution | 2025 | 3825 | 25038 | 0.0034235786364755 | 13.091764705882351 | 322 | 3299 | 0.862483660130719 |

## Centrality Results

Top degree researchers:

| display_name | author_id | main_institution_name | degree_centrality | weighted_degree |
| --- | --- | --- | --- | --- |
| Yu Qiao | A5100748135 | Shanghai Artificial Intelligence Laboratory | 0.0036961175365376 | 438.0 |
| Ji-Rong Wen | A5025631695 | Renmin University of China | 0.0033727072520906 | 316.0 |
| Yih Chung Tham | A5085096438 | Singapore National Eye Center | 0.0033111052931483 | 293.0 |
| James Zou | A5005779176 | Stanford University | 0.0030184959881724 | 271.0 |
| Tianming Liu | A5100647156 | University of Georgia | 0.0029876950087012 | 489.0 |
| Yang Liu | A5100355692 | Nanyang Technological University | 0.0029568940292301 | 232.0 |
| Xipeng Qiu | A5044665993 | Fudan University | 0.0028490906010811 | 316.0 |
| Percy Liang | A5025255782 | Stanford University | 0.0028182896216099 | 278.0 |
| Tien Yin Wong | A5072258594 | Tsinghua University | 0.0027258866831965 | 238.0 |
| Zhengliang Liu | A5101505879 | Mayo Clinic Hospital | 0.0027258866831965 | 442.0 |

Top betweenness researchers:

| display_name | author_id | main_institution_name | betweenness_centrality | weighted_degree |
| --- | --- | --- | --- | --- |
| Yu Qiao | A5100748135 | Shanghai Artificial Intelligence Laboratory | 0.0296560742710723 | 438.0 |
| Ziwei Liu | A5100406050 | Nanyang Technological University | 0.0274707180449615 | 205.0 |
| Dahua Lin | A5010087030 | Chinese University of Hong Kong | 0.0195374525129801 | 213.0 |
| Caiming Xiong | A5032046813 | Salesforce (United States) | 0.0181571498561954 | 231.0 |
| Chunyuan Li | A5107893340 | Microsoft (United States) | 0.015758614627284 | 206.0 |
| Percy Liang | A5025255782 | Stanford University | 0.0151324587446263 | 278.0 |
| Ji-Rong Wen | A5025631695 | Renmin University of China | 0.0138349263030129 | 316.0 |
| Noah A. Smith | A5088517824 | University of Washington | 0.011965537373754 | 149.0 |
| Jifeng Dai | A5026944066 | Tsinghua University | 0.0111455075437351 | 197.0 |
| Lichao Sun | A5015105117 | Lehigh University | 0.0108648322351541 | 154.0 |

Top eigenvector researchers:

| display_name | author_id | main_institution_name | eigenvector_centrality | weighted_degree |
| --- | --- | --- | --- | --- |
| Jared Kaplan | A5053213601 | Anthropic | 0.223541731915177 | 385.0 |
| Sam McCandlish | A5054887773 | Anthropic | 0.2105942596540665 | 329.0 |
| Amanda Askell | A5030305998 | Anthropic | 0.2104217273369257 | 357.0 |
| Anna Chen | A5056436767 | Anthropic | 0.2027486182928939 | 313.0 |
| Kamal Ndousse | A5028970835 | Anthropic | 0.2023991887150873 | 327.0 |
| Yuntao Bai | A5091860006 | Anthropic | 0.2023717426947143 | 322.0 |
| Shauna Kravec | A5009112681 | Anthropic | 0.2023717426947143 | 322.0 |
| Tom Henighan | A5049786610 | Anthropic | 0.1933779129483021 | 313.0 |
| Nelson Elhage | A5020683620 | Anthropic | 0.1914835791508567 | 284.0 |
| Nicholas Joseph | A5032088236 |  | 0.1907133294282909 | 300.0 |

Top bridge institutions:

| institution_name | institution_id | simplified_institution_category | target_firm_label | betweenness_centrality | weighted_degree |
| --- | --- | --- | --- | --- | --- |
| Stanford University | I97018004 | education | Other | 0.1965713087700567 | 1437.0 |
| Harvard University | I136199984 | education | Other | 0.1432564151160435 | 1451.0 |
| Tsinghua University | I99065089 | education | Other | 0.1404705051595482 | 1054.0 |
| Chinese Academy of Sciences | I19820366 | government | Other | 0.098378643453548 | 1220.0 |
| University of Oxford | I40120149 | education | Other | 0.0913890552409138 | 1006.0 |
| Massachusetts Institute of Technology | I63966007 | education | Other | 0.0708810065925464 | 935.0 |
| Nanyang Technological University | I172675005 | education | Other | 0.0689958693801842 | 714.0 |
| National University of Singapore | I165932596 | education | Other | 0.0684531156695041 | 819.0 |
| University of Hong Kong | I889458895 | education | Other | 0.0630369219592724 | 865.0 |
| Carnegie Mellon University | I74973139 | education | Other | 0.0608090532165819 | 612.0 |

## Institution Type Mixing

| category_pair | edge_count | edge_weight |
| --- | --- | --- |
| company-company | 486 | 677.0 |
| company-education | 4555 | 5872.0 |
| company-government | 207 | 245.0 |
| company-healthcare | 614 | 726.0 |
| company-nonprofit | 266 | 302.0 |
| company-research_institute | 863 | 974.0 |
| company-unknown | 181 | 216.0 |
| education-education | 27611 | 35871.0 |
| education-government | 2660 | 3491.0 |
| education-healthcare | 9394 | 12146.0 |
| education-nonprofit | 2511 | 2911.0 |
| education-research_institute | 9985 | 11912.0 |
| education-unknown | 1745 | 2298.0 |
| government-government | 132 | 181.0 |
| government-healthcare | 429 | 472.0 |
| government-nonprofit | 153 | 157.0 |
| government-research_institute | 992 | 1361.0 |
| government-unknown | 128 | 185.0 |
| healthcare-healthcare | 2992 | 3601.0 |
| healthcare-nonprofit | 631 | 754.0 |

Additional edge mixing methods:

| method | category_pair | edge_count | edge_weight |
| --- | --- | --- | --- |
| researcher_edges_author_year_primary_categories | company-company | 28262 | 28262.0 |
| researcher_edges_author_year_primary_categories | company-education | 18969 | 18969.0 |
| researcher_edges_author_year_primary_categories | company-government | 279 | 279.0 |
| researcher_edges_author_year_primary_categories | company-healthcare | 1336 | 1336.0 |
| researcher_edges_author_year_primary_categories | company-nonprofit | 791 | 791.0 |
| researcher_edges_author_year_primary_categories | company-research_institute | 4009 | 4009.0 |
| researcher_edges_author_year_primary_categories | company-unknown | 14938 | 14938.0 |
| researcher_edges_author_year_primary_categories | education-education | 146193 | 146193.0 |
| researcher_edges_author_year_primary_categories | education-government | 2238 | 2238.0 |
| researcher_edges_author_year_primary_categories | education-healthcare | 14129 | 14129.0 |
| researcher_edges_author_year_primary_categories | education-nonprofit | 4301 | 4301.0 |
| researcher_edges_author_year_primary_categories | education-research_institute | 34147 | 34147.0 |
| researcher_edges_author_year_primary_categories | education-unknown | 32521 | 32521.0 |
| researcher_edges_author_year_primary_categories | government-government | 483 | 483.0 |
| researcher_edges_author_year_primary_categories | government-healthcare | 141 | 141.0 |
| researcher_edges_author_year_primary_categories | government-nonprofit | 52 | 52.0 |
| researcher_edges_author_year_primary_categories | government-research_institute | 1572 | 1572.0 |
| researcher_edges_author_year_primary_categories | government-unknown | 475 | 475.0 |
| researcher_edges_author_year_primary_categories | healthcare-healthcare | 7427 | 7427.0 |
| researcher_edges_author_year_primary_categories | healthcare-nonprofit | 503 | 503.0 |
| researcher_edges_author_year_primary_categories | healthcare-research_institute | 2232 | 2232.0 |
| researcher_edges_author_year_primary_categories | healthcare-unknown | 2921 | 2921.0 |
| researcher_edges_author_year_primary_categories | nonprofit-nonprofit | 7121 | 7121.0 |
| researcher_edges_author_year_primary_categories | nonprofit-research_institute | 949 | 949.0 |
| researcher_edges_author_year_primary_categories | nonprofit-unknown | 1735 | 1735.0 |
| researcher_edges_author_year_primary_categories | research_institute-research_institute | 50148 | 50148.0 |
| researcher_edges_author_year_primary_categories | research_institute-unknown | 10157 | 10157.0 |
| researcher_edges_author_year_primary_categories | unknown-unknown | 140083 | 140083.0 |
| papers_all_observed_affiliation_categories | company-company | 336 | 336.0 |
| papers_all_observed_affiliation_categories | company-education | 1700 | 1700.0 |

## Report-Ready Filtered Visualizations

The full network figures are too dense for detailed interpretation and should be treated as overview figures only. The following report-ready figures use filtered backbone, ego-network, and community-level views to make group structure and bridge roles easier to inspect.

- `outputs/figures/report_institution_backbone.png`: largest connected component of the institution network, filtered to high weighted-degree institutions, high betweenness institutions, and target AI firms; edges below weight 2 are dropped unless they connect a target AI firm to education or research institute nodes.
- `outputs/figures/report_company_academic_subnetwork.png`: company to education/research institute collaboration backbone, keeping the strongest company-academic edges and target AI firms.
- `outputs/figures/report_bridge_institution_ego_network.png`: ego networks around the top bridge institutions by betweenness, keeping strongest neighbors.
- `outputs/figures/report_bridge_researcher_ego_network.png`: ego networks around the top bridge researchers by betweenness, keeping strongest coauthors.
- `outputs/figures/report_institution_community_network.png`: Louvain community-level aggregation of the institution network, with community labels based on top institutions.
- `outputs/figures/researcher_network_full_overview.png` and `outputs/figures/institution_network_full_overview.png`: structural overview figures with labels limited to top betweenness nodes.

Visualization validation summary:

| figure | nodes | edges | labeled_nodes |
| --- | --- | --- | --- |
| report_institution_backbone | 96 | 300 | 31 |
| report_company_academic_subnetwork | 81 | 250 | 62 |
| report_bridge_institution_ego_network | 63 | 91 | 22 |
| report_bridge_researcher_ego_network | 96 | 96 | 20 |
| report_institution_community_network | 15 | 80 | 15 |
| researcher_network_full_overview | 300 | 2722 | 20 |
| institution_network_full_overview | 300 | 10291 | 20 |

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
- Report-ready visualization summary: `outputs/figures/report_ready_visualization_summary.json`
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
