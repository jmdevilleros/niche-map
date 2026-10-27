# Coding rubric: MCP servers and agent skills (v1.1)

This rubric is the only material a coder needs. Code each item from its public pages (the linked repository or folder, its README, its `SKILL.md`, its install docs) and nothing else. Do not look at anyone else's codes.

## 1. What counts as an item

An item is **one public package whose main purpose is to give an AI agent a capability**, in one of two forms:

- an **MCP server**: a program or hosted endpoint that speaks the Model Context Protocol;
- an **agent skill**: a folder with a `SKILL.md` (instructions, optionally with scripts and reference files) that an agent loads when relevant.

Out of scope: SDKs, clients, frameworks, specifications, lists, templates and starter repos, and repositories whose main deliverable is an app, CLI, library or platform that merely ships a skill or MCP server as an add-on.

*Scope rule (v1.1).* A vendor's MCP server for its own hosted service **is in scope** when the MCP (or agent) interface is a primary, documented way to use the service, even if the service is a full platform. It is out of scope only when the MCP server or skill is a secondary extra to a product meant to be used by hand (an app, IDE, editor or CLI). If a repository bundles many skills, the item is the one skill named in the link, or, when the link is the repository root, the bundle's headline purpose.

## 2. General decision rules

1. **Code the primary mode.** Use the item's headline promise: the first sentence of its description, `SKILL.md` description or README. Secondary features do not change the code.
2. **Code what the item does for the agent, not how it looks** (a skill that renders a pretty HTML page whose purpose is to explain an answer is still coded by what it produces and for whom).
3. **When two values seem to apply,** use the precedence order given for that dimension.
4. **Ordinal anchors are measured from the install instructions** (the README "Install" / "Quick start" section, or the skill's stated requirements). If they are missing, code the most common case for that kind of item and write `uncertain` in `coding_flag`.
5. Every cell must hold exactly one value from the lists below (lower case, as written).

## 3. Dimensions

### Concept dimensions (what the item is)

**`kind`** — the form of the package.

| value | definition | example |
|---|---|---|
| `mcp` | An MCP server (local process or hosted endpoint). If the repo offers both an MCP server and a skill, and the MCP server is the main deliverable, code `mcp`. | GitHub's official MCP server |
| `skill` | An agent skill (`SKILL.md` package). | Anthropic's `pdf` skill |

**`action`** — the main verb: what the agent does with the item. Precedence when two apply: `coordinate` > `remember` > `execute` > `operate` > `create` > `analyze` > `retrieve` > `guide`.

| value | definition | example |
|---|---|---|
| `retrieve` | Looks up, searches or fetches information from a source at run time, read-only. | a web-search or weather MCP server |
| `operate` | Creates, updates, deletes or sends something in an existing app, service or repository (CRUD, messages, deployments, commits). | a CRM or Kubernetes MCP server |
| `execute` | Runs code, commands, browsers, tests or tools in a sandbox and returns the results. | a code-sandbox server; a Playwright testing skill |
| `create` | Produces a new artifact: document, slide deck, image, audio, video, diagram, web page, font, new skill files. | a spreadsheet-building skill |
| `analyze` | Evaluates, computes, reviews, verifies or diagnoses something the user provides and returns an assessment or result. | a code-review skill; a math-optimization server |
| `remember` | Persists and recalls context across sessions (memory, knowledge base, project memory that the agent writes). | a vector-store memory server |
| `guide` | Teaches the agent how to work: conventions, best practices, framework or SDK know-how, a methodology. No own data source, no new artifact type of its own. | a Python style-guide skill |
| `coordinate` | Orchestrates or governs other agents or tools: gateways, routers, policy/approval layers, multi-agent coordination, delegating work to other models or agent teams. | a policy gate for coding agents |

Decision rules for `action` (v1.1, added after the blind re-coding):

- **A1. Any write in the headline wins.** If the headline lists a write operation (tag, edit, add, send, create a record), code `operate` (or the higher value the precedence gives), even if most tools are reads.
- **A2. Index vs memory.** An index or graph built automatically from an existing source (a codebase, a docs site, a catalogue) that the agent queries is `retrieve`, even if it persists on disk. Code `remember` only when the agent itself writes new facts or decisions for later sessions.
- **A3. Know-how vs artifact (`guide` vs `create`).** Code `create` when the skill outputs a named artifact type with its own format (deck, document, diagram, figure, font, video, blog post, standalone page) and the skill defines how to produce it (steps, templates or scripts). Code `guide` when the skill supplies the rules of a framework, platform, SDK or design system to apply while the agent builds or edits code or content of any kind, even if its description says "create", "build" or "design".
- **A4. SDK and package skills.** A skill that teaches the agent to use a specific SDK, package or CLI is `guide`, even when it ships helper scripts. Code `execute` only when its headline is to run something and report the result (tests, checks, benchmarks) with its own runner.

**`domain`** — the subject area of the data or system the item touches (not the user's industry). Rules: code the subject matter of the content, not its visual form (an anatomy figure → `knowledge_pro`; a binary debug-format analyzer → `software`, unless its stated purpose is security); databases, cloud services, DNS, VPS and their SDKs → `infra_data`; source code, repositories, CI, app frameworks, testing → `software`; notes and personal knowledge vaults → `docs_office`; LLMs, agents, MCP/skill tooling, reasoning aids → `agent_meta`.

| value | definition | example |
|---|---|---|
| `software` | Source code, repos, CI, frameworks, dev docs, testing, feature flags | a CI-status server |
| `infra_data` | Cloud platforms, databases, data platforms, DevOps, domains, hosting | a Postgres best-practices skill |
| `web` | The open web: pages, search engines, browsing | a fetch server |
| `docs_office` | Documents, spreadsheets, slides, local files, notes / PKM | a Word-document skill |
| `comms_social` | Messaging, email, phone, notifications, meetings, social networks, news communities | a Slack server |
| `business` | CRM, ads, marketing, SEO, ERP, project management, sales, startup funding | an ads-analytics server |
| `finance` | Markets, investing, crypto, payments, filings | a stock-research server |
| `knowledge_pro` | Science, health, biology, law, education, academic writing, engineering knowledge | a legal-search server |
| `media_design` | Images, audio, video, UI/visual design, color, art, interactive fiction | an image-generation server |
| `everyday` | Personal life: travel, maps, time, fitness, games, movies, home, astrology | a time-zone server |
| `security` | Security tooling, audits, verification of signed artifacts | a pentest-tools server |
| `agent_meta` | The agent itself: memory, reasoning, LLM access/prices, MCP or skill tooling | a prompt-library skill |

**`user`** — the main human beneficiary, as stated or implied by the item. Rules: if the item is about software, infrastructure or security work, code `developer` (security engineers count as developers); if no profession is targeted, code `general`.

| value | definition |
|---|---|
| `developer` | software engineers, DevOps, security engineers, agent builders |
| `analyst` | researchers, scientists, data/ML/finance analysts, domain experts (lawyers, engineers, students writing theses) |
| `business` | marketers, sales, founders, PMs, operations and office workers |
| `creator` | designers, writers, video/audio/media creators |
| `general` | anyone, or individuals in their personal life |

**`output`** — where the result of a typical successful use lands. Precedence: `external` > `file` > `chat`.

| value | definition |
|---|---|
| `chat` | information, analysis or guidance returned into the conversation; nothing persists outside it |
| `file` | a new or modified file or artifact in the user's workspace (documents, code, images, local memory files) |
| `external` | a state change in a remote system or app (record created, message sent, post published, deployment, live diagram in an app) |

**`mode`** — how the item is used over time. Precedence: `ambient` > `procedure` > `session` > `lookup`.

| value | definition |
|---|---|
| `lookup` | single, stateless call-and-answer (or a set of independent tools, each used that way) |
| `session` | stateful interaction across many calls (a browser, editor or database session; memory that is written and read back) |
| `procedure` | a multi-step workflow the agent follows (phases, checklists, pipelines) |
| `ambient` | always-on or automatic: applied whenever relevant without being called (conventions, rules), runs in the background or reacts to events (hooks, gates, scheduled or monitoring jobs) |

*Mode rule (v1.1).* A skill that is loaded by keywords and whose content is reference rules applied while working is `ambient`; a skill the user invokes to run a sequence of steps is `procedure`.

### Attribute dimensions (how it is built or distributed)

**`runs_where`** (ordinal 0-2) — what has to run, from the install instructions.

| value | anchor |
|---|---|
| `0` | Instructions only: no code of its own runs (a skill with text and reference files; it may tell the agent to use common CLIs such as `git` or `gh`). |
| `1` | Local code: a process, script, binary, container or package that the user installs and runs (`npx`, `uvx`, `docker`, bundled scripts, a dedicated CLI). |
| `2` | Remote endpoint: the documented primary install is a hosted URL; nothing to run locally (a stdio proxy to a hosted service still counts as 2). |

Consistency: a skill is never `2`; an MCP server is never `0`.

*Runs-where rule (v1.1).* For a skill, code `1` when its `SKILL.md` tells the agent to run code bundled with the skill (`python scripts/...`, `node .../build.mjs`). Bundled files the instructions never call, such as repository build, test, CI or eval scripts and templates copied into the output, do not count. Check the file tree, not only the README.

**`auth`** (ordinal 0-2) — what the user must provide before core features work.

| value | anchor |
|---|---|
| `0` | Nothing (optional keys for higher limits do not count). |
| `1` | An API key, token, connection string or account ID pasted into config, or an existing CLI login (`gh auth`). |
| `2` | An interactive OAuth/sign-in flow, or a paid account or purchase is mandatory. |

*Auth rules (v1.1).* Read the "Requirements" / "Prerequisites" / configuration section, not only the headline. A **free** API key that is required still counts as `1`. If the core function (for example, really sending email) needs a paid plan and only a sandbox or demo is free, code `2`. A required commercial program with a free trial counts by its key or login (`1`), not as a purchase.

**`license`** — from the license file of the item's folder if present, else the repository license. *(v1.1)* A license stated explicitly in the `SKILL.md` front matter or the README counts as stated, even without a license file.

| value | definition |
|---|---|
| `permissive` | MIT, Apache-2.0, BSD, ISC, or a mix of these |
| `copyleft` | GPL, AGPL, LGPL, MPL, CC BY-SA |
| `none` | no license file, "all rights reserved", source-available or proprietary terms, or a license GitHub cannot identify and the files do not state |

**`maintainer`** — who publishes it, relative to what it is about.

| value | definition |
|---|---|
| `lab` | the protocol steward or an AI-model lab publishing first-party items (the MCP organization, Anthropic, OpenAI) |
| `vendor` | the organization that owns the product, API or hosted service the item mainly exposes (including a company whose own hosted service is the item's backend) |
| `community` | anyone else: individuals, third-party companies, consultancies, or standalone open-source projects with no separate commercial service behind them |

## 4. Sheet format

Fill one row per item, keeping `id`, `name` and `link`, and add these columns in this order:
`kind, action, domain, user, output, mode, runs_where, auth, license, maintainer`.
Optionally add `coding_flag` (write `uncertain` when an anchor could not be observed) and `notes` (your doubts, in your own words).

## 5. Limits

Codes are judgments. Two careful coders can disagree on overlapping values (`analyze` vs `create`, `guide` vs `create`, `procedure` vs `ambient` for convention skills). The precedence orders exist to make those calls repeatable; when they still do not settle a case, code the primary mode and note the doubt.

## 6. Changelog

- **v1.1 (27 Oct 2026).** After a blind re-coding of 15 items (`action` below threshold): added action rules A1-A4, a scope rule for vendor platforms, a mode rule for keyword-loaded skills, auth rules for required free keys and paid core functions, a license rule for licenses stated in `SKILL.md`/README, a subject-matter rule for `domain`, and a runs-where rule for bundled scripts. The corpus was swept with these rules, and 14 code cells in 12 items changed, plus one link update (listed in WALKTHROUGH.md §8).
- **v1.1 re-check (27 Oct 2026).** A fresh blind re-check of `action` on 15 new items gave 93% agreement, κ 0.92. **Known open gap:** when a product is a panel of several models that returns a verdict on the user's question, `coordinate` ("delegating work to other models") and `analyze` ("returns an assessment") overlap. No rule was added; code the primary mode and note the doubt.
- **v1.0 (27 Oct 2026).** First version.

---
© 2026 Juan Manuel de Villeros. CC BY 4.0.
