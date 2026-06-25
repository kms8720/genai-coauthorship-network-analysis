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
