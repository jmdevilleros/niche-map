---
name: niche-map
description: Find empty niches in any domain by building a quantitative concept map of ~50-150 real items (products, apps, games, services, tools, papers...). Items are coded on 8-15 explicit dimensions with a written rubric and a blind re-coding check; the map comes from Ward clustering, PCA gradients and UMAP (visualization only); gaps are found as absent value combinations and low-density zones, filtered by the target user's profile, translated into concrete ideas and validated against the market with a mirage test. Use it when someone asks "what is missing in this market/genre?", "where is there room for a new product?", "map the landscape of X and show me the gaps", or wants product ideas backed by a verifiable corpus. Do NOT use it to size a market in money, to profile a single competitor, or to extract jobs-to-be-done from interviews.
version: 1.0.0
license: CC-BY-4.0 (this document); MIT (code)
---

# Niche map: gaps in a conceptual space

This skill finds well-founded gaps in a domain. It turns a fuzzy landscape into a table of **real items × explicit dimensions**, looks for combinations and zones nobody occupies, translates those gaps into concrete ideas and checks that they are not mirages.

**Guiding principle.** Numbers organize judgment; they do not replace it. Codes are analyst decisions, so the space reflects the rubric as much as the market. That is why every proposed gap must survive a reliability check on the codes (step 2b) and an external validation (step 6).

**Tools in this repo**

| File | Role |
|---|---|
| `niche_core.py` | Steps 3-4: encoding, clusters, PCA, UMAP, triple gaps, density gaps, candidate neighbors, supply vs demand, figures |
| `recode_check.py` | Step 2b: blind re-coding sample sheet and per-dimension agreement (Cohen's kappa) |
| `md_to_pdf.py` | Step 7: Markdown report to PDF |
| `templates/report_template.md` | Step 7: report skeleton |
| `examples/` | Synthetic, fictional dataset to test the pipeline end to end |

---

## 0. Inputs and scoping questions

Get these answers before starting. If any is missing, ask once, in a single block.

| Input | Question | Why it matters |
|---|---|---|
| Topic and boundary | What counts as an item? (e.g. "tools whose core value is X") | Prevents mixed categories and gap artifacts. |
| N | How many items? (default 80-100; useful minimum ≈ 50) | With N < 50 triple counts are noise. |
| Inclusion criteria | Minimum reception, availability, platform, language, date | Applied in step 1 and documented. |
| Target user | Who will build or buy what comes out? | Basis of the fit score and of `target_filter`. |
| Constraints | Budget, hours, skills, sales channel, excluded topics | Become `target_filter` and the fit criterion. |
| Deliverable | Language, currency (and exchange-rate source), format | Default: PDF with ranking, niche cards, maps and the full corpus table with links. |

## 1. Corpus: N real, verified items

1. **Broad seed.** Collect about 1.3 × N candidates from varied sources: domain stores or directories, "best of" lists, "X alternative" searches and **recent long-tail launches** (launch sites, niche directories, open-source registries). If only famous products get in, false gaps appear later.
2. **Existence check per item.** Each item needs a URL that resolves: store page, pricing page or repository. Record the HTTP status, final URL and date. If a site blocks bots (403), check the domain root or use a browser; a block does not mean the item does not exist.
3. **Reception signal.** Record one or more public signals (store rating and review count, launch-site votes, repository stars, installs, awards) and declare the **source and coverage** of each. Do not drop an item only because it has no signal. If reception is an inclusion criterion, apply it with an explicit threshold.
4. **Deduplicate** variants, rebrands, editions and regional SKUs. Keep the canonical name and links.
5. **Exclude by boundary** the items that fail the inclusion criteria, and list them in the report with the reason.
6. **Corpus bias checks** (write the answers in the report):
   - Share of items from the long tail (e.g. launched in the last 24 months, or below the median reception signal). If it is under ~20 %, sample more long-tail items.
   - Source concentration: no single source should contribute more than ~40 % of items.
   - Platform or language skew relative to the stated boundary.
   - Signal coverage per source (some sources over-represent certain user types, e.g. developer tools on code-hosting sites).

Output: `items.csv`, one row per item with identification and link columns, plus a raw JSON of the verification.

## 2. Dimensions, scales and coding rubric

1. **Derive 8-15 dimensions** by reading a sample of about 20 items. Split them into two types:
   - **Concept dimensions** say *what the item is*: verb or action, input, output, trigger, domain or theme, user, aesthetic. Gaps are searched with these (`gap_dims`).
   - **Attribute dimensions** say *how it is built or sold*: complexity, breadth, self-serve, pricing model, price tier. They filter and score. If used in the gap search they produce **"meta" gaps** such as "event-triggered + no AI + high complexity".
2. **Scales.** Nominal categories with 3-14 mutually exclusive values, each with a readable label, or short ordinals (0-1, 0-2, 1-3) with described anchors.
3. **Written rubric:** one line per value with a definition and an example item, plus the decision rules below. It goes in the report appendix and is the only material the second coder receives in step 2b.
   - **Code the logical structure, not the rendering.** For spatial or structural dimensions, code how the user actually interacts with or reasons about the thing, not how it looks (e.g. a 3D-rendered product used on a flat plane is not "3D").
   - **Precedence order for overlapping values.** When a nominal scale describes something perceptual or stylistic (look, tone, style), values overlap. Give an explicit decision order ("if A applies, code A; else if B..."), or merge values that coders cannot tell apart.
   - **Measurable anchors for ordinals.** Anchors such as duration, size or effort must say how to measure them and from what source (e.g. "typical session as stated in the store description or observed in a demo video; for level-based items, one level"). If it cannot be observed, code the modal case and flag it.
   - **Code the primary mode.** If an item is ambiguous, code its main mode and note the doubt in a `notes` column.
4. **Weights.** Default 1.0. Raise core concept dimensions (e.g. verb to 1.2), lower peripheral ones (e.g. pricing model to 0.4). Justify each weight.
5. **Structural checks:**
   - No category with fewer than 2 items; merge or drop it (`niche_core.py` warns).
   - Cross-tabs to detect redundant dimensions (correlation ≈ 1): drop or merge one of them.
6. **Acknowledge the limits:** codes are judgments.

Output: the items × dimensions CSV and `config.json` with scales, weights and rules.

### 2b. Blind re-coding check (mandatory)

Purpose: measure whether the rubric, not the coder's memory, determines the codes. Gaps built on unreliable dimensions are rubric artifacts.

1. **Sample.** Randomly draw 10 % of the corpus, minimum 10 items, with a fixed seed:
   `python recode_check.py sample --items items.csv --config config.json --out recode_sheet.csv --keep link`
   The sheet contains only the item id and link, with empty dimension columns.
2. **Second coder, blind.** A different person, or a separate agent session that has **never seen the first codes** (no access to `items.csv`, the clusters or the report), codes the sheet using only the written rubric and the item's public pages. If the same agent must do it, start a fresh context and give it only the sheet and the rubric. Lock the result before comparing (e.g. store a checksum).
3. **Agreement per dimension:**
   `python recode_check.py agree --items items.csv --config config.json --recode recode_sheet.csv --out agreement.csv`
   - Categorical dimensions: Cohen's kappa (κ).
   - Ordinal dimensions: linearly weighted Cohen's kappa (κw), which gives partial credit for near misses.
   - Raw percentage agreement is reported alongside, plus a per-item disagreement list.
4. **Threshold.** A dimension passes with κ (or κw) ≥ 0.60 **and** raw agreement ≥ 80 %. With n ≈ 10 kappa is noisy: use it to triage, and read every disagreement.
5. **Below threshold**, in this order:
   1. Read the disagreements and classify them: rubric ambiguity (overlapping values, unmeasurable anchor), rendering vs structure confusion, or coder error.
   2. Fix the rubric with one of the decision rules in step 2.3 (precedence order, measurable anchor, merge values that cannot be told apart).
   3. Re-code that dimension for the **whole corpus** with the revised rubric, then re-run the check on a fresh 10 % sample (new seed) for that dimension.
   4. If it still fails: lower its weight (≤ 0.6), remove it from `gap_dims`, or drop it. Never report a gap whose explaining triple rests on a dimension that failed twice.
6. **Report** the table (dimension, n, % agreement, κ/κw, status), the rubric changes made, and the second coder's identity type (human, separate agent).

Typical outcome: dimensions about function (action, goal, input/output, trigger) agree well; perceptual or estimated dimensions (style, spatial structure, duration) are the usual failures, which is why the decision rules in step 2.3 exist.

## 3. Space: encoding, clusters, gradients and visualization

Done by `niche_core.py`. Golden rule: **clusters and gaps are computed in the original coded space; UMAP is for drawing only.**

- **Encoding.** One-hot × weight/√2 for categorical dimensions and (x − min)/(max − min) for ordinals, so switching category costs the same as an end-to-end ordinal move.
- **Clusters.** Agglomerative Ward with k chosen by silhouette within `k_range`. A larger k is accepted only if it improves silhouette by more than 0.005.
  - **k-range check:** if the chosen k falls on **either edge** of the range, widen the range and re-run; the script warns. If it stays on the edge, choose k by interpretability and say so.
  - Silhouette between 0.15 and 0.30 is normal with categorical data; do not sell it as "crisp clusters".
  - Clusters with < 3 items and items with identical vectors are flagged; the latter suggest a rubric too coarse to distinguish items.
  - Name each cluster by hand from `cluster_profiles.md` and store the names in `cluster_names`.
- **Gradients.** PCA loadings (PC1-PC3, `pca_loadings.csv`) are read as axes "from A to B".
- **Visualization.** UMAP (n_neighbors 10-15, min_dist 0.25, fixed seed) with a KDE density background. Limits:
  - global distances and island sizes mean nothing;
  - `transform` tends to pull new points onto the nearest island, so a candidate's novelty is read from `dist_min` in the original space, never from the plot.
- **Pairwise heatmaps** of dimensions show empty cells at a glance.

## 4. Gaps

**4a. Combinatorial gaps (triples).** For each triple of values of the gap (concept) dimensions, compare observed with expected under independence: e = N · p(a) · p(b) · p(c), z = (e − o)/√e. A triple is kept if:
- o ≤ `max_observed` (default 1);
- e ≥ `min_expected` (default 1.2);
- **every pair** in the triple appears in at least `min_pair_support` items (default 2): the pieces exist separately;
- it touches at least one **anchor dimension** (`anchor_dims`, e.g. domain or verb).

**Meta-gap filter:** keep attribute dimensions out of `gap_dims`, and set `anchor_dims` to the dimensions that describe the product's content. Triples made only of attributes are not niches.

**4b. Density gaps.** 50,000-400,000 random synthetic vectors are generated and kept only if:
1. every pair of values exists in at least one real item (recombination of known pieces);
2. no coherence rule forbids them (`rules`: combinations absurd in the domain);
3. they match the **target user profile** (`target_filter`, e.g. complexity ≤ 1 and self-serve = 1). This is the **user-fit filter**: without it, density gaps drift toward products the user cannot build or sell.

Survivors are ranked by distance to the nearest real item and deduplicated on the main concept dimensions (`density_dedupe`). Compare with the median nearest-neighbor distance between distinct real items (`median_nn_distance`).

**4c. Supply vs demand (optional).** Per cluster: number of items (supply) vs the median of a demand signal (reviews, installs, search volume, stars), always with its coverage (`supply_demand_clusters.csv`). A small cluster with high demand is a gap hint **(inference)**.

**4d. Preliminary score.** Novelty (1-5, from relative distance and the triple that explains the gap), feasibility (1-5, MVP effort with the user's resources) and fit (1-5, preferences and constraints from step 0). For each candidate, check its 3 nearest neighbors by adding it to `candidates` and re-running.

## 5. Semantic translation: from vector to idea

Pick 8-12 candidates from the highest-z triples and the farthest density gaps; merge signals and drop duplicates. Each candidate gets:
- **Working name** and a 2-3 sentence concrete **pitch**: what the user does, what the product delivers.
- **Vector** on all dimensions; must satisfy the rules.
- **Nearest items** with distance (× median).
- **Why it looks empty in the corpus:** which triple or zone explains it, and whether any of its dimensions failed step 2b.
- **Risks:** technical, market and fit.

## 6. External validation and mirage test

1. **Targeted search per candidate**, outside the corpus:
   - "[concept] + app/tool + pricing";
   - "[concept] alternative";
   - domain stores with 2-3 synonyms;
   - open-source repositories.

   Record 3-5 competitors with link and price. **Assume some will almost always appear:** a corpus of N ≈ 100 does not cover the long tail. Adjust novelty accordingly.
2. **Mirage test** (adapted from *white-space-analysis*, see References). The candidate faces four questions:
   - **Size:** are there enough people with this job to be done?
   - **Willingness to pay or switch:** from strongest to weakest evidence, they already pay for a partial solution, keep a costly workaround, or tried to build it themselves.
   - **Incumbent question:** why has nobody filled it? Acceptable answers: business-model or channel conflict, a recent external change, a growing segment. Alarming answer: "I cannot find a reason".
   - **Winnability:** can the target user overcome the barrier that keeps the gap empty?

   Verdict: **pass** (factor 1.0), **doubtful** (0.7) or **fail** (0.4).
3. **Final score** = novelty × feasibility × fit × mirage factor (range 0.4-125).
4. Candidates that fall in validation **stay in the report** as "false gaps". They expose corpus bias and save the reader time.

## 7. Deliverable

A PDF in the user's language plus its Markdown source (skeleton in `templates/report_template.md`, rendered with `md_to_pdf.py`), in this order:
1. Cover and summary: top 3-5 ideas in 1-2 lines each, overall reading of the map, caveats.
2. How the method was applied: N, sources, corpus bias checks, dimensions, re-coding agreement table, k, silhouette, number of gaps.
3. Maps: UMAP with density, PCA biplot with gradients, heatmaps, absent-triple bars, supply vs demand table.
4. Ranking: distance, neighbors, scores, mirage verdict and MVP effort **(estimate)**.
5. Niche cards: pitch, vector, neighbors, why it is empty, validation with links, mirage test, suggested price and risks.
6. False gaps, limitations and lessons.
7. Appendices: the rubric (with changes from step 2b) and **the full corpus table with links**.

Conventions:
- Never invent figures: mark **(estimate)** what you computed and **(inference)** what you deduced.
- Money in the user's local currency plus USD, with exchange rate, date and source.
- Render the pages to PNG and inspect them before delivering: split tables, overlaps, cut text.

## Data licensing and republication

- A corpus should contain **public facts** (names, URLs, published prices) and your own codes. Your codes are your work.
- **Do not republish third-party store ratings, review counts or install numbers in bulk** (app stores, launch sites and review sites restrict scraping and redistribution). In a public artifact keep only the link, or an aggregate with date and source.
- Do not copy descriptions, reviews, screenshots or logos.
- Trademarks belong to their owners; use them nominatively.
- Keep raw verification dumps (page HTML, API responses) private.

## Tool reference: `niche_core.py`

```
python niche_core.py --items items.csv --config config.json --out out/ [--samples 400000] [--compare ref.csv] [--no-figs]
```
The config declares:
- `id_col`; `categorical` (values, weight, labels) and `ordinal` (range), optional `ordinal_weights`;
- `gap_dims`, `anchor_dims` and `rules` (forbidden combinations, operators ==, !=, in, not_in, >=, <=);
- `target_filter`, `k_range`, `seed`, `umap_neighbors`, `min_pair_support`, `min_expected`, `max_observed`, `density_dedupe`;
- `heatmap_pairs`, `label_items`, `cluster_names`, `demand_cols` and `candidates`.

Outputs:
- tables: `clusters.csv`, `cluster_profiles.md`, `silhouette.csv`, `pca_loadings.csv`, `triple_gaps.csv`, `density_gaps.csv`, `density_gaps_top.csv`, `candidate_neighbors.csv`, `supply_demand_clusters.csv`;
- figures: `fig_umap.png`, `fig_pca.png`, `fig_heatmaps.png`, `fig_gaps.png`;
- `summary.json`.

## Common errors and limitations

- **Rubric gaps.** A badly defined category creates gaps that do not exist. Countermeasures: step 2b and step 6.
- **Corpus bias.** Famous products over-represented, long tail missing: false gaps. Countermeasures: step 1.6 and "alternative" searches in step 6.
- **A gap is not an opportunity.** It may be empty because nobody pays for it. That is what the mirage test is for.
- **Meta gaps.** Attribute dimensions in the triples. Use concept dimensions in `gap_dims` and set `anchor_dims`.
- **Low silhouette and edge k** are normal with categorical data. Do not over-interpret cluster boundaries.
- **UMAP** is for drawing only. Never measure novelty on it.
- **Reception signals:** some review sites block automated access; some sources skew toward particular user types. Declare coverage.
- **Independence as null hypothesis:** correlated dimensions inflate z. Use z to rank, not as a statistical test.
- **Ideas are recombinations of existing pieces.** The method does not invent new dimensions; an innovation that breaks the rubric will not appear.

## Estimated time (estimate, agent-assisted, N ≈ 100)

| Step | Time |
|---|---|
| 0 Scope | 10-20 min |
| 1 Corpus and verification | 2-4 h |
| 2 Rubric and coding | 1.5-3 h |
| 2b Blind re-coding and fixes | 30-60 min |
| 3-4 Analysis (script) | 15-30 min, plus reading |
| 5 Translation | 45-90 min |
| 6 Validation | 1-2 h |
| 7 Report and visual review | 1-1.5 h |
| **Total** | **≈ 7.5-13 h** |

## Quality checklist

- [ ] Every item has a verified link (HTTP status, date) and a reception source, or "no signal" declared.
- [ ] Exclusions documented; corpus bias checks (long-tail share, source concentration, skew, coverage) answered.
- [ ] Written rubric with decision rules; no category with < 2 items.
- [ ] Blind re-coding of ≥ 10 % (min 10 items) by a coder blind to the first codes; κ/κw and % agreement per dimension reported; dimensions below threshold fixed, re-checked, down-weighted or dropped.
- [ ] Concept and attribute dimensions separated; `anchor_dims` and `target_filter` defined.
- [ ] k not on the edge of `k_range`, or justified; clusters have human names.
- [ ] Novelty measured in the original space; UMAP used only to visualize.
- [ ] Each candidate has neighbors, distance, an external search with 3-5 linked competitors and a mirage verdict.
- [ ] False gaps appear in the report.
- [ ] Every non-observed figure is marked **(estimate)** or **(inference)**; exchange rate has date and source.
- [ ] No bulk third-party ratings or installs in any public artifact.
- [ ] PDF pages rendered and inspected; full corpus table with links included.

## References and related work

- **[SkillMedev / white-space-analysis](https://github.com/SkillMedev/skills/blob/main/skills/white-space-analysis/SKILL.md):** qualitative jobs-to-be-done analysis crossing importance and satisfaction, validating each gap with four tests against the *mirage gap*. **Adopted** here as the mirage test in step 6.
- **[mloki23 / market-gap-finder](https://github.com/mloki23/market-gap-finder):** qualitative web research scored on five dimensions (demand evidence, competitive vacuum, revenue potential, accessibility, timing), without a vector space.
- **["Stargazing Agent Skills in the Latent Space" (S. Cohen, 2026)](https://shmulc.substack.com/p/stargazing-agent-skills-in-the-latent):** embeds a large set of agent skills, visualizes them with UMAP and clusters in the original space. An analysis, not a reusable skill. **Lesson made explicit here:** cluster and compute gaps in the original space; UMAP only visualizes.
- **Cohen, J. (1960).** A coefficient of agreement for nominal scales. *Educational and Psychological Measurement*, 20(1), 37-46. **Cohen, J. (1968).** Weighted kappa. *Psychological Bulletin*, 70(4), 213-220.
- **Landis, J. R. & Koch, G. G. (1977).** The measurement of observer agreement for categorical data. *Biometrics*, 33(1), 159-174 (κ 0.61-0.80 = "substantial").

**What this skill adds:** explicit, rubric-coded and auditable concept dimensions (instead of opaque embeddings) with a formal blind reliability check; combinatorial (triple) and density gaps with coherence and user-fit constraints; semantic translation of each gap into an idea with neighbors; external validation with a mirage test; optional supply vs demand per cluster.

## Version history

- **0.1:** first formalization of the method from a private study.
- **0.2:** revised after a field test in a second domain: concept vs attribute dimensions and `anchor_dims` (meta gaps); `target_filter` (user fit); long-tail sampling and "alternative" searches (several candidates turned out to be false gaps); mirage test with multiplier; k-edge warning; supply vs demand; UMAP.transform caveat; signal coverage.
- **1.0.0:** English, generic. Formal blind re-coding step (2b) with Cohen's kappa and `recode_check.py`, rubric decision rules derived from a real re-coding check; corpus bias checks; lower-edge k warning; identical-vector warning; synthetic example; data-licensing section.
