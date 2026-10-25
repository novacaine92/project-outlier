# Project Outlier | AI Research Team v0.1

A **research-only** starter for three specialist roles: SCOUT, QUANT, SKEPTIC, coordinated by OUTLIER COMMAND.

## Quick start

Requires Python 3.10+; no third-party packages for default mode.

```bash
python -m unittest discover -s tests -v
python engine.py
```

Read `reports/latest.md` for the synthetic research report. The sample prices are **fictional** and are not real market opportunities.

## Optional AI commentary

The default pipeline uses deterministic agent logic and makes **no paid API calls**. To enable separate LLM reviews for the three roles, configure an OpenAI API key securely as an environment variable and set `OUTLIER_USE_AI=1`. This invokes the Responses API and **may incur charges**. `OUTLIER_MODEL` defaults to `gpt-4.1-mini`; choose an available model for your account. Never commit API keys. The included GitHub workflow deliberately does not enable AI calls or require secrets.

## GitHub Actions

`.github/workflows/research.yml` supports manual runs and a weekly scheduled run. It tests the code, generates a report from fictional data, and uploads the report as a workflow artifact. Workflow schedules are best-effort and not a continuous service. GitHub Actions may have usage limits and costs depending on account/repository configuration.

## Safety boundaries

- No trading, transfers, wallets, or brokerage integration.
- No live data ingestion until data rights, jurisdiction, fee schedules, settlement equivalence, and executable quotes have been reviewed.
- Positive theoretical spreads are **not** proof of executable arbitrage.
- Never put private financial information or secrets in a public repository.
- Human authorization required for spending, deployments, and any future live execution.

## Next steps

1. Get GitHub write access working, or upload the starter through GitHub's web interface.
2. Run tests and the sample pipeline.
3. Select a legitimate data API and document the market contract semantics.
4. Build a read-only live-data adapter, timestamped audit trail, and realistic paper-trading harness.
5. Introduce AI reviews only after deterministic tests work, with a small explicit API budget.
