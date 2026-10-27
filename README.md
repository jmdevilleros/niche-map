# niche-map

A reusable, domain-agnostic research method (an agent skill) plus Python tools to **find empty niches in any market**: products, apps, games, services, tools, publications.

You collect ~50-150 real items, code them on 8-15 explicit dimensions with a written rubric, check the rubric with a blind re-coding, and the tools build a map (Ward clusters, PCA gradients, UMAP for visualization only), detect combinatorial and density gaps filtered by your own constraints, and help you turn them into concrete ideas that you then validate against the market with a mirage test.

- **Method:** [`SKILL.md`](SKILL.md) (steps 0-7, scoring, deliverable spec, checklist).
- **Status:** v1.0.0.

## Contents

| Path | What it is |
|---|---|
| `SKILL.md` | The method, with agent-skill frontmatter (`name: niche-map`) |
| `niche_core.py` | Items CSV + `config.json` → clusters, PCA loadings, triple gaps, density gaps, candidate neighbors, supply vs demand, figures, `summary.json` |
| `recode_check.py` | Blind re-coding: sample sheet + per-dimension agreement (Cohen's kappa, weighted kappa for ordinals) |
| `md_to_pdf.py` | Markdown report → PDF (WeasyPrint) |
| `templates/report_template.md` | Report skeleton for step 7 |
| `examples/` | **Synthetic, fictional** dataset and config to test the pipeline |

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python niche_core.py --items examples/synthetic_items.csv --config examples/config.json --out out/example
```

Then read `out/example/cluster_profiles.md`, `triple_gaps.csv`, `density_gaps_top.csv` and the figures.

For a new domain:
1. Build `items.csv`: one row per real item, one column per dimension, plus id and link columns.
2. Write `config.json` (format documented in the header of `niche_core.py` and in `SKILL.md`).
3. Run the blind re-coding check: `recode_check.py sample`, have a blind second coder fill the sheet, then `recode_check.py agree`. Fix dimensions below threshold.
4. Run `niche_core.py`, name the clusters, add `candidates`, run again.
5. Validate candidates externally, score them, and write the report from `templates/report_template.md`; render with `python md_to_pdf.py report.md report.pdf --footer "..."`.

### Using it as an agent skill

Copy this folder into your agent's skills directory (or point the agent to `SKILL.md`). The frontmatter `description` tells the agent when to use it.

## Related work

- [SkillMedev / white-space-analysis](https://github.com/SkillMedev/skills/blob/main/skills/white-space-analysis/SKILL.md): JTBD importance vs satisfaction with a *mirage gap* test, which this method adopts in its validation step.
- [mloki23 / market-gap-finder](https://github.com/mloki23/market-gap-finder): qualitative web research scored on five dimensions, without a vector space.
- [Stargazing Agent Skills in the Latent Space (S. Cohen, 2026)](https://shmulc.substack.com/p/stargazing-agent-skills-in-the-latent): embeddings + UMAP + clustering of agent skills. Shared lesson: cluster and measure in the original space; UMAP only visualizes.

What this adds: explicit, auditable rubric-coded dimensions with a formal blind reliability check, combinatorial and density gaps with coherence and user-fit filters, idea translation with neighbors, and market validation with a mirage test.

## Third-party data

Corpora you build should hold public facts (names, URLs, published prices) and your own codes. Do not republish store ratings, review counts or install numbers in bulk; link to the source instead. See the data-licensing section of `SKILL.md`. This repository contains no real research data: the example is synthetic.

## License

- Code (`*.py`): **MIT**, see [`LICENSE`](LICENSE).
- Documentation (`SKILL.md`, `README.md`, `templates/`, `examples/README.md`) and the synthetic example data: **CC BY 4.0**, see [`LICENSE-docs`](LICENSE-docs).

© 2026 Juan de Villeros
