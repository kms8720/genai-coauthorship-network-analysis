# Institution Classification Rules

This project first uses the OpenAlex `type` field when available, then applies conservative string matching to produce two inspectable labels:

- `simplified_institution_category`
- `target_firm_label`

## Simplified Categories

- `company`: OpenAlex type contains `company`, or institution name clearly matches a known commercial AI firm.
- `education`: OpenAlex type contains `education`.
- `research_institute`: OpenAlex type contains `facility`, `archive`, or `repository`, or name contains clear research-lab terms.
- `government`: OpenAlex type contains `government`.
- `nonprofit`: OpenAlex type contains `nonprofit`.
- `healthcare`: OpenAlex type contains `healthcare`.
- `unknown`: no reliable match.

## Target Firm Labels

The scripts conservatively match institution names for:

- OpenAI
- Google / Google DeepMind / DeepMind
- Meta
- Microsoft
- Anthropic
- Apple
- Amazon
- NVIDIA
- Cohere
- Mistral AI
- xAI
- Stability AI
- Hugging Face
- Other

Ambiguous names are left as `Other` rather than guessed.

