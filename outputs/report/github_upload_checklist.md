# GitHub Upload Checklist

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

`Update generative AI coauthorship network analysis outputs`

## Exact Git Commands

From the project root:

```bash
git add .
git commit -m "Update generative AI coauthorship network analysis outputs"
git push origin main
```

If this is a fresh local clone with no remote configured:

```bash
git remote add origin https://github.com/kms8720/genai-coauthorship-network-analysis.git
git branch -M main
git push -u origin main
```

Do not push automatically unless the user explicitly requests upload.
