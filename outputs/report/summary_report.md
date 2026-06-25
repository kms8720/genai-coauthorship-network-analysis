# Generative AI Research Ecosystem: Competition and Collaboration in Firm-University Coauthorship Networks

## Research Question

Is the generative AI research ecosystem organized as a closed firm-centered competitive structure, or as a mixed/collaborative structure connected through universities, research institutions, and mobile researchers?

## Data Collection Summary

- Source: OpenAlex Works API
- Environment variables: `OPENALEX_API_KEY=not set; OPENALEX_EMAIL=not set`
- Raw file: `data/raw/openalex_works_raw.jsonl`
- Processed works: 16000
- Unique authors: 64934
- Unique institutions: 7416
- Works by year: `{"2022": 3524, "2023": 4040, "2024": 4219, "2025": 4217}`

Limitations: this sample-mode dataset depends on keyword search terms and OpenAlex affiliation metadata. Search terms may miss relevant papers that do not use the selected terminology, and affiliations can be incomplete or ambiguous.

Betweenness centrality uses exact calculation when network size is feasible and sampling approximation only when node counts exceed `max_exact_betweenness_nodes` in `config.yaml`. Degree, weighted degree, and eigenvector centrality are calculated directly. Community labels use Louvain when available.

Centrality method summary:

| network | year | node_count | edge_count | betweenness_method | betweenness_k |
| --- | --- | --- | --- | --- | --- |
| researcher | full | 64934 | 312015 | approximate_weighted_brandes_sampling | 300 |
| institution | full | 7416 | 71371 | exact_weighted_igraph | 0 |
| researcher | 2022 | 16777 | 66924 | approximate_weighted_brandes_sampling | 300 |
| institution | 2022 | 3219 | 24360 | exact_weighted_igraph | 0 |
| researcher | 2023 | 17455 | 85562 | approximate_weighted_brandes_sampling | 300 |
| institution | 2023 | 2602 | 15015 | exact_weighted_igraph | 0 |
| researcher | 2024 | 21419 | 96424 | approximate_weighted_brandes_sampling | 300 |
| institution | 2024 | 2944 | 14960 | exact_weighted_igraph | 0 |
| researcher | 2025 | 21782 | 89296 | approximate_weighted_brandes_sampling | 300 |
| institution | 2025 | 3818 | 24974 | exact_weighted_igraph | 0 |

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
| institution | full | 7416 | 71371 | 0.002595798044868 | 19.247842502696876 | 550 | 6680 | 0.9007551240560948 |

Year-by-year:

| network | year | node_count | edge_count | density | average_degree | connected_components | largest_component_size | share_nodes_largest_component |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| institution | full | 7416 | 71371 | 0.002595798044868 | 19.247842502696876 | 550 | 6680 | 0.9007551240560948 |
| institution | 2022 | 3219 | 24360 | 0.004703273814523 | 15.135135135135137 | 359 | 2677 | 0.8316247281764523 |
| institution | 2023 | 2602 | 15015 | 0.0044371865488972 | 11.541122213681785 | 350 | 2060 | 0.7916986933128363 |
| institution | 2024 | 2944 | 14960 | 0.0034532937404895 | 10.16304347826087 | 328 | 2420 | 0.8220108695652174 |
| institution | 2025 | 3818 | 24974 | 0.0034273623294535 | 13.08224201152436 | 323 | 3290 | 0.8617077003666841 |

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
| Tien Yin Wong | A5072258594 | Singapore National Eye Center | 0.0027258866831965 | 238.0 |
| Zhengliang Liu | A5101505879 | University of Georgia | 0.0027258866831965 | 442.0 |

Top betweenness researchers:

| display_name | author_id | main_institution_name | betweenness_centrality | weighted_degree |
| --- | --- | --- | --- | --- |
| Yu Qiao | A5100748135 | Shanghai Artificial Intelligence Laboratory | 0.0296560742710723 | 438.0 |
| Ziwei Liu | A5100406050 | Nanyang Technological University | 0.0274707180449615 | 205.0 |
| Dahua Lin | A5010087030 | Chinese University of Hong Kong | 0.0195374525129801 | 213.0 |
| Caiming Xiong | A5032046813 | Salesforce (United States) | 0.0181571498561954 | 231.0 |
| Chunyuan Li | A5107893340 | Microsoft Research (United Kingdom) | 0.015758614627284 | 206.0 |
| Percy Liang | A5025255782 | Stanford University | 0.0151324587446263 | 278.0 |
| Ji-Rong Wen | A5025631695 | Renmin University of China | 0.0138349263030129 | 316.0 |
| Noah A. Smith | A5088517824 | University of Washington | 0.011965537373754 | 149.0 |
| Jifeng Dai | A5026944066 | Shanghai Artificial Intelligence Laboratory | 0.0111455075437351 | 197.0 |
| Lichao Sun | A5015105117 | Lehigh University | 0.0108648322351541 | 154.0 |

Top eigenvector researchers:

| display_name | author_id | main_institution_name | eigenvector_centrality | weighted_degree |
| --- | --- | --- | --- | --- |
| Jared Kaplan | A5053213601 |  | 0.223541731915177 | 385.0 |
| Sam McCandlish | A5054887773 |  | 0.2105942596540665 | 329.0 |
| Amanda Askell | A5030305998 | Saudi Heart Association | 0.2104217273369257 | 357.0 |
| Anna Chen | A5056436767 |  | 0.2027486182928939 | 313.0 |
| Kamal Ndousse | A5028970835 |  | 0.2023991887150873 | 327.0 |
| Yuntao Bai | A5091860006 |  | 0.2023717426947143 | 322.0 |
| Shauna Kravec | A5009112681 |  | 0.2023717426947143 | 322.0 |
| Tom Henighan | A5049786610 |  | 0.1933779129483021 | 313.0 |
| Nelson Elhage | A5020683620 |  | 0.1914835791508567 | 284.0 |
| Nicholas Joseph | A5032088236 |  | 0.1907133294282909 | 300.0 |

Top bridge institutions:

| institution_name | institution_id | simplified_institution_category | target_firm_label | betweenness_centrality | weighted_degree |
| --- | --- | --- | --- | --- | --- |
| Stanford University | I97018004 | education | Other | 0.1957143470521797 | 1426.0 |
| Harvard University | I136199984 | education | Other | 0.1430162018186441 | 1450.0 |
| Tsinghua University | I99065089 | education | Other | 0.1404972533896318 | 1052.0 |
| Chinese Academy of Sciences | I19820366 | government | Other | 0.0987189692767885 | 1220.0 |
| University of Oxford | I40120149 | education | Other | 0.0914373090480965 | 1003.0 |
| Massachusetts Institute of Technology | I63966007 | education | Other | 0.0708620995946392 | 933.0 |
| Nanyang Technological University | I172675005 | education | Other | 0.0690628972860336 | 714.0 |
| National University of Singapore | I165932596 | education | Other | 0.0687002324727467 | 816.0 |
| University of Hong Kong | I889458895 | education | Other | 0.0631251464433831 | 861.0 |
| Carnegie Mellon University | I74973139 | education | Other | 0.060980512796392 | 610.0 |

## Institution Type Mixing

| category_pair | edge_count | edge_weight |
| --- | --- | --- |
| company-company | 439 | 606.0 |
| company-education | 4384 | 5637.0 |
| company-government | 201 | 235.0 |
| company-healthcare | 598 | 707.0 |
| company-nonprofit | 254 | 286.0 |
| company-research_institute | 840 | 947.0 |
| company-unknown | 177 | 212.0 |
| education-education | 27611 | 35871.0 |
| education-government | 2660 | 3491.0 |
| education-healthcare | 9403 | 12157.0 |
| education-nonprofit | 2504 | 2903.0 |
| education-research_institute | 9985 | 11912.0 |
| education-unknown | 1743 | 2295.0 |
| government-government | 132 | 181.0 |
| government-healthcare | 430 | 473.0 |
| government-nonprofit | 153 | 157.0 |
| government-research_institute | 992 | 1361.0 |
| government-unknown | 127 | 184.0 |
| healthcare-healthcare | 3004 | 3613.0 |
| healthcare-nonprofit | 633 | 756.0 |

## Evidence Related to Hypotheses

- H1. Partial firm-centered clustering: inspect `target_firm_label`, community labels, and institution network figures. A supported claim requires visible firm-centered communities plus cross-community links.
- H2. Limited direct firm-to-firm collaboration: inspect `outputs/tables/firm_to_firm_edges.csv`.
- H3. Universities and research institutions as bridges: inspect `outputs/tables/potential_bridge_institutions.csv` and company-education rows in `institution_type_edge_mixing.csv`.
- H4. Degree and betweenness may differ: compare `top_researchers_degree.csv` and `top_researchers_betweenness.csv`.
- H5. Increasing connectedness over time: compare density, component count, and largest-component share in `network_summary_by_year.csv`.

## What To Inspect Manually Next

- Top bridge researchers' career histories and affiliation changes.
- Whether bridge roles come from researcher mobility, joint appointments, or large multi-institution papers.
- Institution classification rules in `institution_classification_rules.md`, especially ambiguous organizations.
- Papers with large author lists that were excluded from pairwise researcher edges by the configurable threshold.

## Files Generated

- Processed tables: `data/processed/`
- Network tables: `outputs/networks/`
- Gephi files: `outputs/gephi/`
- Metric tables: `outputs/tables/`
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
