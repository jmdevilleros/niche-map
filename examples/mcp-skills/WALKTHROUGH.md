# Worked example: 144 public MCP servers and agent skills

This folder is a full, reproducible run of the niche-map method on a real public market: **Model Context Protocol (MCP) servers and agent skills** (`SKILL.md` packages). Everything here can be rebuilt from `items.csv` and `config.json`. Codes follow rubric **v1.1**, which was revised after the blind re-coding (section 8).

**Question.** Among the capabilities people publish for AI agents, which combinations of *what it does, on what, for whom, and how* are missing or sparse, and which of those holes are real?

**Short answer.** Of nine candidate gaps, one passed the mirage test: **an MCP server that watches infrastructure and pushes events to the agent** (G9). Three were doubtful and five were false gaps, meaning things that already exist but were not in the sample.

| file | what it is |
|---|---|
| `items.csv` | the corpus: `id, name, link` + our codes on 10 dimensions (+ `coding_flag`) |
| `config.json` | dimensions, weights, rules, candidate gaps, cluster names |
| `RUBRIC.md` | the coding rubric (self-contained, used for the blind re-coding) |
| `candidates.csv` | candidate gaps with novelty, feasibility, fit, mirage verdict and final score |
| `results/` | outputs of `niche_core.py` (clusters, silhouette, PCA loadings, triple gaps, density gaps, candidate neighbors) |
| `figures/` | the six figures explained below |
| `make_figures.py` | rebuilds every figure from the files above |

Reproduce:

```bash
python niche_core.py --items examples/mcp-skills/items.csv   # needs the duplicate-tolerance fix noted in section 2 --config examples/mcp-skills/config.json --out examples/mcp-skills/results
python examples/mcp-skills/make_figures.py
```

---

## 1. Scope and corpus

**Item boundary.** One public package whose main purpose is to give an AI agent a capability, either as an MCP server or as an agent skill (full definition in `RUBRIC.md` §1). SDKs, clients, lists, templates, specs, and apps that ship a skill as an add-on are out of scope.

**Sampling (seeded, verified on 27 Oct 2026, America/Bogota).** Random draws with fixed seeds, not hand-picked favourites:

| source | kept | share |
|---|---:|---:|
| awesome-mcp-servers (punkpeye), random non-official entries | 40 | 27.8% |
| awesome-mcp-servers, random entries tagged official | 14 | 9.7% |
| GitHub topic search (`agent-skills`, `claude-skill`), single-skill repos | 29 | 20.1% |
| Official MCP Registry, random latest entries with a GitHub repo | 23 | 16.0% |
| Vendor skill repos (Vercel, Hugging Face, Cloudflare, Supabase, Microsoft, Trail of Bits, K-Dense, obra) | 16 | 11.1% |
| anthropics/skills | 10 | 6.9% |
| MCP reference servers (modelcontextprotocol/servers) | 7 | 4.9% |
| openai/skills | 5 | 3.5% |
| **total** | **144** | 84 MCP, 60 skills |

**Corpus checks.**

- **Source concentration.** The largest source, awesome-mcp-servers, contributes 37.5% when its two strata are combined. That is under the 40% cap, but close to it.
- **Long tail.** About half of the items (73 of 144) sit in their own repository with fewer than 100 GitHub stars, and 104 repositories were created in the last 12 months. The sample is not a list of famous projects.
- **Known skews.**
  - Everything here is hosted on GitHub.
  - Skills found by topic search lean toward popular repos, because search ranks by popularity, while the MCP Registry and awesome-list entries are mostly tiny.
  - Skills in the lab and vendor folders share one monorepo each, so they carry no reception signal of their own.
- **Size.** N=144 is a little above the 100-130 that was planned, because fewer candidates were excluded than expected. We kept all of them rather than drop items by hand.

**Exclusions (22 of 166 candidates).** Reasons:

- **MCP Registry, 11 of 34 sampled.**
  - 8 repository links returned 404. That is 24% link rot among the sampled registry entries, which is a finding in itself.
  - 2 were unmodified templates.
  - 1 had no README at all.
- **Topic search, 11.** The primary deliverable was not a skill or MCP server:
  - a CLI (3)
  - an IDE or editor app (2)
  - a resume app
  - a vector database
  - lint rules
  - a skills-builder platform
  - a specification
  - a multi-product collection with no headline purpose

**What the public files contain.** Each row of `items.csv` holds only `id, name, link` and our own codes. No README text, list descriptions or per-item star counts are republished. Star counts were used privately, and only as aggregates (section 5).

## 2. Dimensions and weights

| dimension | type | values | weight | why this weight |
|---|---|---|---:|---|
| `kind` | concept | mcp, skill | 1.0 | the basic form; already strongly tied to `mode` and `output` |
| `action` | concept | retrieve, operate, execute, create, analyze, remember, guide, coordinate | 1.2 | the main verb is the core of the "concept" (validated by a second blind check, section 8) |
| `domain` | concept | 12 areas | 1.0 | what it touches |
| `user` | concept | developer, analyst, business, creator, general | 0.8 | partly implied by domain |
| `output` | concept | chat, file, external | 0.8 | partly implied by action |
| `mode` | concept | lookup, session, procedure, ambient | 0.8 | partly implied by kind |
| `runs_where` | attribute, ordinal 0-2 | instructions / local code / hosted | 0.6 | how it is delivered, not what it is |
| `auth` | attribute, ordinal 0-2 | none / key / OAuth or paid | 0.5 | friction, not concept |
| `license` | attribute | permissive, copyleft, none | 0.4 | context only |
| `maintainer` | attribute | lab, vendor, community | 0.6 | who can credibly build it |

Gaps are searched only on the six concept dimensions, with `action` and `domain` as anchors. Attributes are fixed on candidates so they describe a plausible community project: permissive license, community maintainer, local code, no auth. G9 needs an API token.

**Forbidden combinations** (`rules`). These are excluded from the density search because they are impossible by definition:

- a skill that is hosted (`runs_where` = 2)
- an MCP server with no code (`runs_where` = 0)
- `remember` with `chat` output
- `guide` with `external` output
- `guide` used as a `lookup`

The density search is also restricted to community, low-auth vectors (`target_filter`).

**Structural checks.**

- **Identical vectors.** 12 groups (29 items) share a full vector. Examples:
  - the vendor framework-guidance skills (Cloudflare sandbox, Supabase, two Azure SDK skills)
  - four coding-conventions skills
  - three code-context MCP servers (gitingest, CodeGraphContext, codebase-memory)
  - Anthropic's xlsx and docx skills

  These are real near-duplicates of concept, not rubric errors. They do mean the rubric cannot tell, for example, "Supabase know-how" from "Azure SDK know-how" apart. That is deliberate, because domain is coarse. (`niche_core.py` v1.0 compares distances to exactly zero and under-counts these as 10; it also lets those near-zero values into the reference median. The results here use a one-line tolerance fix, `nnd < 1e-6`. Without it, relative distances read about 5% too high.)
- **Correlated dimensions (Cramér's V).**
  - kind–mode 0.82
  - action–output 0.82
  - kind–action 0.74
  - domain–user 0.72
  - kind–output 0.71

  None of them is redundant (V < 0.9), so all were kept. The correlations are strong enough to inflate the z-score of combinations that cut across them. For example, "an MCP server that creates files" is rare partly because MCP and files are rarely paired at all. Read triple z-scores with that in mind.

## 3. Structure: clusters and gradients

**k = 8, silhouette = 0.245** (Ward on weighted one-hot, k tested from 4 to 16). k=8 is the maximum, with k=9 close behind at 0.244 (a larger k must beat the best by more than 0.005). A value of 0.24 is normal for categorical codes: the groups are real but they overlap.

| cluster | name | n | profile |
|---|---|---:|---|
| C0 | Operators | 28 | MCP servers that change external systems: CRM, messaging, cloud, project tools |
| C1 | Memory & stateful sessions | 9 | Memory servers and skills, sandboxes |
| C2 | Lookups | 32 | Read-only MCP servers that answer one question at a time |
| C3 | Artifact makers | 24 | Skills that write files: documents, slides, images, video, sites |
| C4 | Developer workflow skills | 12 | Testing, CI, debugging, review and deployment procedures |
| C5 | Analyzers | 14 | MCP servers that compute, verify or assess |
| C6 | Guidance skills | 19 | Conventions and framework know-how, applied ambiently |
| C7 | Coordinators | 6 | Agent governance: gateways, policy gates, delegation |

Full counts per dimension are in `results/cluster_profiles.md`.

**PCA (results/pca_loadings.csv).** The first three components explain 25%, 11% and 10% of the variance.

- **PC1** runs from *skill / file / create / procedure* to *MCP / lookup / retrieve / chat*. It is the main split of the market, between packages that make things and servers that answer things.
- **PC2** runs from *retrieve / chat* to *operate / external*, which is reading the world versus changing it.

## 4. How to read each figure

**`figures/fig_umap.png` — map.**
- Each dot is one item, coloured by its Ward cluster.
- Grey contours show how densely real items are packed.
- Stars are the nine candidate gaps, coloured by mirage verdict: green = pass, orange = doubtful, grey = false gap.
- UMAP is for drawing only (n_neighbors 12, min_dist 0.25, seed 42). Distances on the picture are approximate, and the stars are projected with `UMAP.transform`. Every number in this walkthrough is computed in the original coded space.
- What to see: three land masses. The skills (C3 artifact makers, C4 developer workflow, C6 guidance) form one band. The MCP servers that read or compute (C2 lookups, C5 analyzers, C7 coordinators), together with memory (C1), form another. C0 operators form their own island. Where UMAP puts each island on the page carries no meaning. G9 sits in the thin strip between analyzers and lookups.

**`figures/fig_pca.png` — gradients.**
- Shows the items on PC1 × PC2, with arrows for the strongest loadings.
- Use it to name the axes of the market (see section 3). It is not meant for finding clusters.

**`figures/fig_silhouette.png` — choice of k.**
- Plots silhouette against k, with the chosen k marked.
- The curve is flat between 7 and 9 and drops after 9. Any k in 7-9 tells the same story.

**`figures/fig_heatmaps.png` — pair counts.**
- Observed counts for four pairs: action × domain, domain × user, action × mode and action × output.
- Empty cells are only a starting point. Many are empty for a reason; for example, `guide` × `external` is impossible by definition.
- Things to see:
  - *create* concentrates in media and documents
  - *operate* concentrates in business, comms and infra
  - *analyze* is spread thinly over many domains

**`figures/fig_gaps.png` — triple gaps.**
- The concept triples with the largest shortfall between expected and observed counts: z = (e − o)/√e, keeping only triples whose three pairs each appear at least twice.
- Bars show the expected count; labels give z.

**`figures/fig_candidates.png` — scores.**
- Final score = novelty × feasibility × fit × mirage factor, with each score from 1 to 5.
- The mirage factor is 1.0 for pass, 0.7 for doubtful and 0.4 for fail. Each bar is labelled with the four factors.

## 5. Supply vs demand (aggregate, private data)

Demand signal: GitHub stars of the item's **own** repository, read on 27 Oct 2026. Items in shared monorepos have no signal of their own and are left out. Coverage is the share of each cluster with a signal.

| cluster | supply (n) | median own-repo stars | coverage |
|---|---:|---:|---:|
| C0 Operators | 28 | 0 | 0.93 |
| C1 Memory & sessions | 9 | 84 | 0.78 |
| C2 Lookups | 32 | 6.5 | 0.94 |
| C3 Artifact makers | 24 | 631 | 0.71 |
| C4 Developer workflow skills | 12 | 496.5 | 0.17 |
| C5 Analyzers | 14 | 1 | 0.93 |
| C6 Guidance skills | 19 | 349 | 0.26 |
| C7 Coordinators | 6 | 1.5 | 1.00 |

**Caveats.** Treat this as a weak signal, not a ranking.
- Stars measure attention, not use.
- The skill clusters look popular partly because topic search returns popular repos first (section 1).
- C4 and C6 rest on two and five repos respectively.

The one robust contrast is that MCP servers in C0, C2, C5 and C7 are numerous and almost unstarred. Supply there outruns attention.

## 6. Gaps

**Triple gaps (results/triple_gaps.csv).** 105 coherent triples score above zero. The top ones, with what each means:

| triple | expected | observed | z | reading |
|---|---:|---:|---:|---|
| mcp + create + developer | 6.3 | 0 | 2.51 | no MCP server that produces developer artifacts (diagrams, code, configs) |
| skill + retrieve + developer | 5.7 | 0 | 2.39 | no skill that fetches fresh developer info at run time |
| mcp + analyze + file | 5.1 | 0 | 2.26 | analysis servers never write a report file |
| create + developer + lookup | 4.7 | 0 | 2.16 | one-shot generators for developers |
| mcp + infra_data + file | 3.7 | 0 | 1.91 | infra servers never emit files (e.g. infra as code) |
| mcp + media_design + procedure | 3.6 | 0 | 1.89 | no multi-step media pipeline server |

Several of these partly restate the kind–output and action–output correlations noted in section 2. That is why the candidates below are checked against the outside world.

**Density gaps (results/density_gaps_top.csv).**
- 1,438 feasible synthetic vectors pass the rules and target filter.
- The emptiest lie at distance 1.5-1.65 from the nearest real item, while the median distance from a real item to its nearest *distinct* real item is 0.84.
- Most of them are business or analyst combinations, such as analysis servers that write files for business users, and they overlap with the triples above.

**Candidates.** Nine candidates (G1–G9) were written from the top triples and density zones, each as a full vector (`config.json` → `candidates`). Distances are to the nearest real item in coded space; `rel` is that distance divided by the median distance from a real item to its nearest distinct real item (0.84).

| id | candidate | concept vector | dist (rel) | nearest real items |
|---|---|---|---:|---|
| G1 | Report-writing analysis server | mcp · analyze · docs_office · business · file · procedure | 1.58 (1.89×) | S048, M006, S044 |
| G2 | Fresh-docs retrieval skill | skill · retrieve · software · developer · chat · procedure | 1.28 (1.53×) | M047, M048, M045 |
| G3 | Diagram/codegen server for developers | mcp · create · software · developer · file · lookup | 1.34 (1.60×) | M004, M057, M045 |
| G4 | Design-critique skill | skill · analyze · media_design · creator · chat · procedure | 0.80 (0.95×) | S044, S017, M049 |
| G5 | Infra-to-code generator server | mcp · create · infra_data · developer · file · procedure | 1.41 (1.69×) | S046, S035, S034 |
| G6 | Personal-service operator skill | skill · operate · everyday · general · external · procedure | 1.31 (1.56×) | S018, S059, S012 |
| G7 | Multi-step media pipeline server | mcp · create · media_design · creator · file · procedure | 1.00 (1.19×) | S047, S056, M075 |
| G8 | Systematic-review protocol server | mcp · retrieve · knowledge_pro · analyst · file · procedure | 1.13 (1.35×) | M019, M009, M020 |
| G9 | Event-driven infra watcher server | mcp · analyze · infra_data · developer · chat · ambient (auth 1) | 1.34 (1.60×) | M072, M035, M084 |

## 7. Mirage test

For each candidate we searched the web, GitHub and the MCP Registry for things that already do it, outside the sample. Every link below returned HTTP 200 on 27 Oct 2026.

| id | verdict | what already exists |
|---|---|---|
| G9 | **pass** | Claude Code [channels](https://code.claude.com/docs/en/channels) and TanStack AI [MCP events](https://tanstack.com/ai/latest/docs/tools/mcp-events) make server-pushed events possible. The only implementations found are CI-only or tiny: [cluesmith/ci-channel](https://github.com/cluesmith/ci-channel), [drmf-cz/claude-beacon](https://github.com/drmf-cz/claude-beacon). No general infra/data watcher (alerts, cost spikes, failed jobs, schema drift) was found. |
| G1 | doubtful | Audit servers that write reports exist for MCP itself ([MCPSec](https://github.com/mcp-shark/MCPSec), [mcp-audit](https://github.com/batoisystems/mcp-audit), [change-trace-mcp](https://github.com/Canlendula/change-trace-mcp)), but not a general business-document analysis server. |
| G8 | doubtful | [prismAId MCP](https://prismaid.review/mcp-server), [prisma-review-tool](https://github.com/Black-Lights/prisma-review-tool) and [Ariadne](https://github.com/cgarryZA/Ariadne) cover parts of a PRISMA-style review; none is clearly the full protocol. |
| G6 | doubtful | Errand-style operators exist as CLI + skill bundles ([General Input](https://docs.generalinput.com/cli), [hey-cli skill](https://github.com/basecamp/hey-cli/blob/main/skills/hey/SKILL.md), [Nylas CLI](https://cli.nylas.com/)), but they are tied to one vendor. |
| G2 | fail | [Context7 find-docs skill](https://github.com/upstash/context7/blob/master/skills/find-docs/SKILL.md), [netresearch/context7-skill](https://github.com/netresearch/context7-skill), plus an open [Hermes agent PR](https://github.com/NousResearch/hermes-agent/pull/98178). |
| G7 | fail | [kinocut](https://github.com/kyanitelabs/kinocut), [resolve-mcp-server](https://github.com/guycochran/resolve-mcp-server), [FableCut MCP](https://fablecut.space/docs/mcp/), [CleanAudio podcast MCP](https://cleanaudio.app/mcp/podcast-editing). |
| G4 | fail | [design-review](https://github.com/humbleteam/design-review), [ux-audit-skill](https://github.com/EliaAlberti/ux-audit-skill), [Nielsen heuristics audit](https://github.com/ruanbenade/nielsen-heuristics-audit-with-claude). |
| G3 | fail | [drawio-mcp](https://github.com/jgraph/drawio-mcp), [mermaid-mcp](https://github.com/tci-nebula/mermaid-mcp), [draft1-mcp](https://github.com/abdelhadi-azouni/draft1-mcp), [mcp-uml-diagram](https://github.com/techdeveloper-org/mcp-uml-diagram). |
| G5 | fail | [Terraback MCP](https://terraback.io/mcp/) (with a paid tier), [Azure MCP Terraform export](https://learn.microsoft.com/en-us/azure/developer/azure-mcp-server/tools/azure-terraform), [Firefly MCP](https://www.firefly.ai/academy/terraform-mcp-server). |

**Final scores (candidates.csv).**

| id | novelty | feasibility | fit | mirage | score |
|---|---:|---:|---:|---|---:|
| G9 | 4 | 4 | 4 | pass ×1.0 | **64** |
| G1 | 3 | 4 | 3 | doubtful ×0.7 | 25.2 |
| G8 | 3 | 4 | 3 | doubtful ×0.7 | 25.2 |
| G6 | 3 | 3 | 3 | doubtful ×0.7 | 18.9 |
| G2 | 1 | 5 | 4 | fail ×0.4 | 8 |
| G7 | 2 | 3 | 3 | fail ×0.4 | 7.2 |
| G4 | 1 | 5 | 3 | fail ×0.4 | 6 |
| G3 | 1 | 4 | 3 | fail ×0.4 | 4.8 |
| G5 | 2 | 2 | 2 | fail ×0.4 | 3.2 |

**What the false gaps teach.** The two strongest triple gaps, *mcp + create + developer* (G3) and *skill + retrieve + developer* (G2), are both mirages. The products exist; they were simply not in a 144-item sample. A gap inside the sample is a question to ask the outside world, not an answer.

**The surviving idea, G9.** An MCP server that watches infrastructure and data systems and pushes a short, analysed event to the agent: "nightly job failed, here is why", "spend jumped 40% on X", "schema changed upstream". It sits where the market is thin in two ways:
- most MCP servers are `lookup` (61 of 84), and
- only 5 MCP servers are `ambient`: four coordinators and one scheduled business-research digest. None of them touches infrastructure or data.

The enabling protocol features (server-to-client channels and events) are new in 2026. **Main risk:** client support for pushed events is still limited and uneven, so the idea's timing depends on clients more than on the server.

## 8. Blind re-coding

**Setup.**
- **Sample.** 15 items (10%, minimum 10), drawn with seed 20261027 and spread across MCP servers and skills.
- **Second coder.** A separate AI agent session. It received only `id, name, link`, rubric v1.0 and short instructions, and had no access to `items.csv`, the results or this file. It is not a human coder. The first coder is also an AI agent working under the author's direction, so the check measures whether the *written rubric* leads two independent readings to the same codes. It does not measure agreement between humans.
- **Integrity.**
  - Our original codes for the sample were hashed before the blind pass (SHA-256 `681c507f590ecbb8cc6cf1733fecff6ee5648d2001008a88fb9f6ad6f4e29c8b`). The hash still matched our codes when the recode arrived.
  - The recode's own hash (`f4f82732dbd5a0544b60dd3fa946eff6a492388ed2d340a25ab76a3478fceab8`) matched the file and a read-only copy.
- **Check.** `python recode_check.py agree --items items.csv --config config.json --recode recode_filled.csv --out agreement.csv`. Cohen's κ is used for categorical dimensions and linearly weighted κ for ordinal ones. A dimension passes at κ ≥ 0.60 **and** ≥ 80% raw agreement.

**Results (first codes, rubric v1.0, n = 15).**

| dimension | % agree | κ / κw | status |
|---|---:|---:|---|
| kind | 100.0 | 1.00 | pass |
| action | 73.3 | 0.67 | **fail (raw agreement < 80%)** |
| domain | 100.0 | 1.00 | pass |
| user | 80.0 | 0.73 | pass (at the raw threshold) |
| output | 86.7 | 0.77 | pass |
| mode | 80.0 | 0.70 | pass (at the raw threshold) |
| runs_where | 86.7 | 0.84 (κw) | pass |
| auth | 80.0 | 0.66 (κw) | pass (at the raw threshold) |
| license | 100.0 | 1.00 | pass |
| maintainer | 100.0 | 1.00 | pass |

**Overall:** mean raw agreement **88.7%**, median κ **0.80**. One dimension fails (`action`) and three pass exactly at the 80% line (`user`, `mode`, `auth`). With n = 15, one item moves raw agreement by 6.7 points and κ is noisy, so every disagreement was read (17 cells in 7 items).

**Disagreements and what was done.**

| item | dimension | first → second | classification | action taken |
|---|---|---|---|---|
| M013 | action, output | retrieve → operate, chat → external | first-coder error: the headline says "search, view and **tag**", and precedence puts operate above retrieve | recoded operate / external (rule A1 makes it explicit) |
| M048 | action, output, mode | retrieve → remember, chat → file, lookup → session | rubric ambiguity: a persistent code index vs agent memory | new rule A2 (an automatic index is retrieve); first code kept |
| S029 | action | execute → guide | rubric ambiguity: SDK know-how skill that ships scripts | new rule A4; recoded guide |
| S057 | action, user, mode | guide → create, developer → creator, ambient → procedure | rubric ambiguity: design-system skill whose description says "creates" | new rule A3 (framework/design-system rules are guide); first codes kept |
| M008 | auth, mode | 1 → 2, session → lookup | auth: first-coder error, since real sending needs a paid plan; mode: ambiguity | auth recoded 2; mode kept |
| M013 | auth | 0 → 1 | first-coder error: an API key is listed under Requirements | recoded 1 |
| S029 | auth | 0 → 1 | the HF token is marked optional and only needed for gated downloads | first code kept (0) |
| S051, S060 | runs_where | 0 → 1 | first-coder error: `SKILL.md` tells the agent to run bundled scripts | recoded 1 |
| S051, S060 | user | business → creator, general → analyst | rubric ambiguity: no rule for mixed audiences | first codes kept; flagged |

The coder's notes also flagged doubts on cells where both coders agreed: domain for S060 and S027, mode for S016 and S024, action for S019, and the scope of M008. These led to a domain subject-matter rule, a mode rule for keyword-loaded skills, and a scope rule. **M008 scope decision:** M008 is a vendor platform whose MCP and agent interface is its primary documented way of use, so it stays **in scope** under the v1.1 scope rule. **S016 license:** no LICENSE file, but MIT is stated in `SKILL.md`/README, so `permissive` is kept (rule added). **S029 link:** the repository was renamed and the link now points to `K-Dense-AI/scientific-agent-skills`.

**Rubric v1.1 and corpus sweep.**
- Following the skill, the revised rules were applied to the **whole corpus**, not only to the sample:
  - re-reading the headline and Requirements of every item for the action and auth rules;
  - checking the file tree of every skill coded `runs_where = 0` for scripts its `SKILL.md` calls.
- **Changes: 14 code cells in 12 items, plus one link.**
  - action: M013, S029
  - output: M013
  - auth: M008 →2; M013, M043, M070 and M077 →1 (free keys required)
  - runs_where 0→1: S044, S046, S050, S051, S056, S060
- The sweep found more first-coder errors than the sample did, mainly in `runs_where` and `auth`. The blind pass paid for itself beyond the one failing dimension.

**Effect on the results.**
- **Clusters.** k stays 8, and silhouette moves from 0.238 to 0.245. Clusters are nearly identical (adjusted Rand index 0.93 against the v1.0 run).
- **Gaps.** The top triple gaps are unchanged. Raw candidate distances moved by at most 0.06. Relative distances also fell by about 5% because of the tolerance fix in section 2.
- **Mirage test.** Verdicts do not depend on codes or weights, so the outcome still holds: 1 pass, 3 doubtful, 5 false gaps.

**Status of `action`: failed once, fixed, then passed a fresh blind re-check.**
- Under the skill's rules, a failing dimension is fixed and recoded across the corpus, then re-checked blind on a fresh sample. Only if it fails again is it down-weighted (≤ 0.6), removed from `gap_dims` or dropped.
- Of the four action disagreements in the first check, the new rules sided with the first coder twice (M048, S057) and with the second coder twice (M013, S029). Because the rules were written after seeing those disagreements, the re-check below uses new items and a new coder session.

**Second blind check (`action` only, rubric v1.1).**
- **Sample.** 15 items not in the first sample, drawn with seed 20261029.
- **Coder.** A new, separate AI agent session. It received only `id, name, link`, rubric v1.1 and instructions.
- **Integrity.**
  - Our `action` codes for these items were hashed before the sheet went out (SHA-256 `71c96df5819dcb1f11a846741be930574ab81a17750eb0da362ab8256e651c54`). They were unchanged when the recode came back.
  - The recode's hash (`ca9918a13f59e8c3f3d797a33327405988b2c4d995d12ca8ddc6528dfeafe6d5`) matched the file and a read-only copy.

| dimension | n | % agree | κ | status |
|---|---:|---:|---:|---|
| action (v1.1) | 15 | 93.3 | 0.92 | **pass** |

- **Result.** 14 of 15 items agree. `action` is now **validated** and keeps its weight of 1.2. No code was changed after this check, so results and figures are those of the v1.1 run above.
- **The one disagreement (M076, a hosted panel of models that debates a user's decision): first coder `analyze`, second coder `coordinate`.** This is a real rubric gap, documented but not fixed. `coordinate` includes "delegating work to other models", and `analyze` includes "returns an assessment". The rubric does not say which wins when the product *is* a multi-model panel that returns a verdict. A v1.2 rule would need its own blind check, so the code stays as first coded.
- **Close calls the coder noted, without disagreeing:**
  - M066 (coordinate vs remember)
  - M038 (retrieve vs analyze)
  - M075 (create vs analyze)
  - S013 (operate vs analyze)
  - S021 (guide vs operate)
  - S015 (create vs guide)

  In each case the coder said the precedence order or rules A1-A4 settled it. For M068, the coder had to read a subfolder README because the root README is sparse.
- **M066 scope decision.** M066 is a self-hosted "context engineering platform" with a web dashboard. Agents use it through MCP ("every agent that connects gets the full picture"), and its MCP server is what the registry lists. Under the v1.1 scope rule, the MCP interface is a primary, documented way to use it, so it stays **in scope**. This is borderline, like M008.

**Sensitivity: what if `action` had failed again?** Kept for the record, we re-ran the analysis with action weighted 0.6.
- **Structure.** It becomes flatter: k = 15 and silhouette 0.205 (the curve keeps rising toward the top of the range). Cluster agreement with the main run is adjusted Rand index 0.32. The cluster map depends on action's weight, so the cluster names above depend on action being reliable, which the second check supports.
- **Gaps.** The triple gaps do not use weights and are unchanged.
- **G9.** G9 stays 1.43× the median distance from its nearest real item, in the upper half of the nine candidates. Its explaining triple (*mcp + infra_data + ambient*) does not involve `action` at all. G9 rests on `mode`, which passed exactly at the threshold, so its re-check matters as much.

## 9. Limitations

- **Judgment codes, AI coders.** Both coders are AI agents, and the blind check (section 8) covers 15 items. `action` failed the first check and passed a fresh re-check after the rubric fix (93%, κ 0.92). `user`, `mode` and `auth` passed only at the threshold and were not re-checked. The overlaps most likely to cause disagreement are guide vs create, index vs memory, and procedure vs ambient.
- **Sample, not census.**
  - 144 items out of thousands.
  - Only GitHub-hosted items.
  - Topic search favours popular skills.
  - The MCP Registry has 24% link rot in our sample, and dead entries were excluded.
- **Correlated dimensions** inflate triple z-scores (section 2).
- **Coarse domain.** Near-duplicate concepts collapse into identical vectors.
- **Stars are a weak demand proxy.** They are only available for items with their own repo, and are reported only as cluster medians.
- **Snapshot.** Everything was verified on 27 Oct 2026. This market changes weekly.

---

© 2026 Juan Manuel de Villeros. Codes, rubric and documentation: CC BY 4.0. Code (`make_figures.py`): MIT. Item names and links point to their owners' public pages; no third-party text is reproduced.
