#!/usr/bin/env python3
# Copyright (c) 2026 Juan Manuel de Villeros. MIT License (see LICENSE at the repository root).
"""
make_figures.py - publication figures for the MCP servers & agent skills worked example.

Recomputes the same space as niche_core.py (same encoding, Ward clusters, PCA, UMAP seed) and draws
cleaner, labelled figures. Novelty is never read from these plots: see candidate_neighbors.csv (dist_min).

    python examples/mcp-skills/make_figures.py            # from the repository root
    python examples/mcp-skills/make_figures.py --x-image out/umap_x.png   # also the 1600x900 social image
"""
import argparse, json, os, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
for cand in (HERE.parents[1], Path(os.environ.get("NICHE_CORE_DIR", "."))):
    if (cand / "niche_core.py").exists(): sys.path.insert(0, str(cand)); break
import niche_core as nc  # noqa: E402

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from scipy.stats import gaussian_kde

PAL = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#7f7f7f"]
VERDICT = {"pass": "#1a9850", "doubtful": "#f39c12", "fail": "#8a8a8a"}
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False})

def label(cfg, dim, v):
    return cfg["categorical"].get(dim, {}).get("labels", {}).get(str(v), str(v))

def build(items, config):
    df, cfg = nc.load(items, config); nc.CFG_ORD = set(cfg["ordinal"])
    X = nc.encode(df, cfg)
    from sklearn.decomposition import PCA
    from sklearn.cluster import AgglomerativeClustering
    import umap
    pca = PCA(n_components=min(6, X.shape[1]), random_state=0).fit(X); P = pca.transform(X)
    um = umap.UMAP(n_neighbors=min(cfg["umap_neighbors"], len(df) - 1), min_dist=.25, random_state=cfg["seed"]).fit(X)
    (s, k, lab), sil = nc.clusters(X, cfg)
    cands = cfg.get("candidates", [])
    XC = nc.encode(pd.DataFrame([c["vec"] for c in cands]), cfg) if cands else None
    UC = um.transform(XC) if cands else None
    PC = pca.transform(XC) if cands else None
    return df, cfg, X, P, pca, um.embedding_, lab, k, s, sil, cands, UC, PC

def umap_axes(ax, df, cfg, U, lab, cands, UC, verdicts, big=False):
    kd = gaussian_kde(U.T, bw_method=.25)
    pad = 1.2
    gx, gy = np.mgrid[U[:, 0].min()-pad:U[:, 0].max()+pad:250j, U[:, 1].min()-pad:U[:, 1].max()+pad:250j]
    z = kd(np.vstack([gx.ravel(), gy.ravel()])).reshape(gx.shape)
    ax.contourf(gx, gy, z, levels=9, cmap="Greys", alpha=.30)
    names = cfg.get("cluster_names", {})
    for c in range(lab.max() + 1):
        m = lab == c
        ax.scatter(U[m, 0], U[m, 1], s=(90 if big else 46), color=PAL[c % 10], edgecolor="white", lw=.7, zorder=3,
                   label=f"{names.get(str(c), 'C'+str(c))} ({m.sum()})")
        cx, cy = np.median(U[m, 0]), np.median(U[m, 1])
        ax.text(cx, cy, f"C{c}", fontsize=(17 if big else 11), weight="bold", color=PAL[c % 10], ha="center", va="center", zorder=4,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec=PAL[c % 10], lw=1.2, alpha=.9))
    if cands is not None and len(cands):
        for i, c in enumerate(cands):
            col = VERDICT.get(verdicts.get(c["id"], ""), "#111")
            ax.scatter(UC[i, 0], UC[i, 1], marker="*", s=(620 if big else 300), color=col, edgecolor="#111", lw=1.0, zorder=7)
            # if another star sits close on the left, put this label below-right; if close on the right, above-left
            span = np.ptp(UC[:, 0]) if len(UC) > 1 else 1.0
            near = [j for j in range(len(UC)) if j != i and np.hypot(*(UC[j] - UC[i])) < .06 * max(span, 1e-9)]
            off = (9, 7)
            if near:
                off = (9, -18) if UC[i, 0] > min(UC[j, 0] for j in near) else (-30, 9)
            ax.annotate(c["id"], UC[i], fontsize=(15 if big else 10), weight="bold", xytext=off, textcoords="offset points", zorder=8,
                        bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=.8))
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(False)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", default=str(HERE / "items.csv")); ap.add_argument("--config", default=str(HERE / "config.json"))
    ap.add_argument("--scores", default=str(HERE / "candidates.csv")); ap.add_argument("--out", default=str(HERE / "figures"))
    ap.add_argument("--x-image", help="also write the 1600x900 social image here")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    df, cfg, X, P, pca, U, lab, k, s, sil, cands, UC, PC = build(a.items, a.config)
    sc = pd.read_csv(a.scores) if os.path.exists(a.scores) else pd.DataFrame(columns=["id", "mirage"])
    verdicts = dict(zip(sc.id, sc.mirage)); N = len(df)

    # 1) UMAP map
    fig, ax = plt.subplots(figsize=(13, 8.5))
    umap_axes(ax, df, cfg, U, lab, cands, UC, verdicts)
    h, l = ax.get_legend_handles_labels()
    h += [Line2D([], [], marker="*", ls="", ms=15, mfc=VERDICT[v], mec="#111") for v in ("pass", "doubtful", "fail")]
    l += ["candidate gap: mirage pass", "candidate gap: doubtful", "candidate gap: false gap (fail)"]
    ax.legend(h, l, fontsize=10, loc="center left", bbox_to_anchor=(1.0, .5), frameon=False, title="Ward clusters (original space)", title_fontsize=11)
    ax.set_title(f"Map of {N} public MCP servers and agent skills (UMAP, visualization only)", loc="left", fontsize=15, weight="bold")
    fig.text(.01, .015, "Grey = density of real items. Stars = candidate gaps placed with UMAP.transform (approximate; novelty is measured as distance in the original coded space).",
             fontsize=9.5, color="#444")
    fig.tight_layout(rect=(0, .03, 1, 1)); fig.savefig(f"{a.out}/fig_umap.png", dpi=170); plt.close()

    # 2) PCA biplot
    ld = pd.DataFrame(pca.components_[:2].T, index=nc.feature_names(cfg), columns=["a", "b"])
    top = ld.assign(n=np.hypot(ld.a, ld.b)).sort_values("n", ascending=False).head(12)
    fig, ax = plt.subplots(figsize=(12, 8.5))
    for c in range(lab.max() + 1):
        m = lab == c; ax.scatter(P[m, 0], P[m, 1], s=40, color=PAL[c % 10], alpha=.75, label=f"C{c} {cfg['cluster_names'].get(str(c), '')}")
    sc_ = 0.8 * np.abs(P[:, :2]).max() / np.abs(top[["a", "b"]].values).max()
    pos = []
    for k_, r in top.iterrows():
        ax.annotate("", xy=(r.a * sc_, r.b * sc_), xytext=(0, 0), arrowprops=dict(arrowstyle="-|>", color="#c0392b", lw=1.6, alpha=.85))
        d, v = k_.split("=") if "=" in k_ else (k_, "")
        pos.append([r.a * sc_ * 1.06, r.b * sc_ * 1.06, f"{d}={label(cfg, d, v)}" if v else d])
    for _ in range(200):   # simple vertical repulsion so labels do not overlap
        moved = False
        for i in range(len(pos)):
            for j in range(i + 1, len(pos)):
                if abs(pos[i][0] - pos[j][0]) < .55 and abs(pos[i][1] - pos[j][1]) < .075:
                    dy = .04 if pos[i][1] >= pos[j][1] else -.04
                    pos[i][1] += dy; pos[j][1] -= dy; moved = True
        if not moved: break
    for x_, y_, t_ in pos:
        ax.text(x_, y_, t_, color="#c0392b", fontsize=10, ha="center", va="center", zorder=4,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=.85))
    if PC is not None:
        for i, c in enumerate(cands):
            ax.scatter(PC[i, 0], PC[i, 1], marker="*", s=240, color=VERDICT.get(verdicts.get(c["id"], ""), "#111"), edgecolor="#111", zorder=5)
            ax.annotate(c["id"], PC[i, :2], fontsize=9, weight="bold", xytext=(5, 4), textcoords="offset points")
    ev = pca.explained_variance_ratio_
    ax.axhline(0, color="#ccc", lw=.8); ax.axvline(0, color="#ccc", lw=.8)
    ax.set_xlabel(f"PC1 ({ev[0]*100:.0f} % of variance)", fontsize=12); ax.set_ylabel(f"PC2 ({ev[1]*100:.0f} % of variance)", fontsize=12)
    ax.set_title("PCA biplot: arrows are the 12 strongest features (read each axis as a gradient from one end to the other)", loc="left", fontsize=13, weight="bold")
    ax.legend(fontsize=9, loc="upper left", bbox_to_anchor=(1.0, 1), frameon=False)
    fig.tight_layout(); fig.savefig(f"{a.out}/fig_pca.png", dpi=170); plt.close()

    # 3) silhouette vs k
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(sil.k, sil.silhouette, "-o", color="#34495e", lw=2)
    ax.scatter([k], [s], s=220, color="#c0392b", zorder=5)
    ax.annotate(f"chosen k = {k}\nsilhouette = {s:.3f}", (k, s), xytext=(-170, 30), textcoords="offset points", fontsize=11, color="#c0392b",
                arrowprops=dict(arrowstyle="-", color="#c0392b"))
    ax.axhspan(.15, .30, color="#2ecc71", alpha=.08); ax.text(sil.k.max(), .155, "0.15-0.30: normal for categorical codes", ha="right", fontsize=9, color="#2c7a4b")
    ax.set_xlabel("k (number of Ward clusters)", fontsize=12); ax.set_ylabel("mean silhouette", fontsize=12); ax.set_xticks(sil.k)
    ax.set_title("Choosing k: a larger k must beat the best silhouette by > 0.005", loc="left", fontsize=13, weight="bold")
    fig.tight_layout(); fig.savefig(f"{a.out}/fig_silhouette.png", dpi=170); plt.close()

    # 4) pair heatmaps
    hp = cfg.get("heatmap_pairs", [])[:4]
    fig, axs = plt.subplots(2, 2, figsize=(16, 13)); axs = axs.ravel()
    for ax, (da, db) in zip(axs, hp):
        ia = cfg["categorical"][da]["values"]; ib = cfg["categorical"][db]["values"]
        t = pd.crosstab(df[da], df[db]).reindex(index=ia, columns=ib, fill_value=0)
        ax.imshow(t.values, cmap="magma_r", aspect="auto", vmin=0, vmax=max(8, t.values.max()))
        ax.set_xticks(range(len(ib)), [label(cfg, db, v) for v in ib], rotation=35, ha="right", fontsize=11)
        ax.set_yticks(range(len(ia)), [label(cfg, da, v) for v in ia], fontsize=11)
        for i in range(t.shape[0]):
            for j in range(t.shape[1]):
                v = t.values[i, j]
                ax.text(j, i, v if v else "·", ha="center", va="center", fontsize=11 if v else 13, color="white" if v >= 6 else "#444")
        ax.set_title(f"{da} × {db}", fontsize=14, weight="bold", loc="left")
        for sp in ax.spines.values(): sp.set_visible(False)
    fig.suptitle("Pair heatmaps: number of items per combination (· = empty cell)", x=.01, ha="left", fontsize=16, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, .97)); fig.savefig(f"{a.out}/fig_heatmaps.png", dpi=150); plt.close()

    # 5) absent triples
    gaps = nc.triple_gaps(df, cfg); g = gaps[gaps.coherent].head(15)
    fig, ax = plt.subplots(figsize=(12, 7.5)); y = np.arange(len(g))[::-1]
    ax.barh(y, g.expected, color="#cfd3e6", label="expected if dimensions were independent")
    ax.barh(y, g.observed, color="#c0392b", label="observed")
    ax.set_yticks(y, [" + ".join(label(cfg, d_, v_) if d_ == "kind" else f"{d_}={label(cfg, d_, v_)}" for d_, v_ in ((r.d1, r.v1), (r.d2, r.v2), (r.d3, r.v3))) for r in g.itertuples()], fontsize=10.5)
    for yi, r in zip(y, g.itertuples()): ax.text(r.expected + .08, yi, f"z={r.z:.2f}", va="center", fontsize=9, color="#555")
    ax.set_xlabel("items", fontsize=12); ax.legend(frameon=False, fontsize=10, loc="upper center", bbox_to_anchor=(.5, -.09), ncol=2)
    fig.suptitle("Top 15 absent combinations (observed ≤ 1, expected ≥ 1.2, every pair of values exists in ≥ 2 items)", x=.01, ha="left", fontsize=13, weight="bold")
    fig.tight_layout(rect=(0, 0, 1, .96)); fig.savefig(f"{a.out}/fig_gaps.png", dpi=170); plt.close()

    # 6) candidate scores
    if len(sc):
        s2 = sc.sort_values("final_score"); fig, ax = plt.subplots(figsize=(11, 6))
        ax.barh(range(len(s2)), s2.final_score, color=[VERDICT[v] for v in s2.mirage])
        ax.set_yticks(range(len(s2)), [f"{r.id}  {r.name}" for r in s2.itertuples()], fontsize=11)
        for i, r in enumerate(s2.itertuples()): ax.text(r.final_score + .8, i, f"{r.final_score:g}  ({r.novelty}×{r.feasibility}×{r.fit}×{r.mirage_factor})", va="center", fontsize=9.5)
        ax.set_xlabel("final score = novelty × feasibility × fit × mirage factor (max 125)", fontsize=11)
        ax.legend([plt.Rectangle((0, 0), 1, 1, color=VERDICT[v]) for v in VERDICT], ["mirage pass", "doubtful", "false gap"], frameon=False, loc="lower right")
        ax.set_title("Candidate gaps after external validation", loc="left", fontsize=13, weight="bold"); ax.set_xlim(0, max(80, s2.final_score.max() + 15))
        fig.tight_layout(); fig.savefig(f"{a.out}/fig_candidates.png", dpi=170); plt.close()

    # social image 1600x900
    if a.x_image:
        fig = plt.figure(figsize=(16, 9), dpi=100); ax = fig.add_axes([.015, .10, .64, .74])
        umap_axes(ax, df, cfg, U, lab, cands, UC, verdicts, big=True)
        fig.text(.02, .935, f"niche-map: {N} MCP servers & agent skills", fontsize=34, weight="bold", color="#111")
        fig.text(.02, .885, "Each dot is a real, public item coded by hand on 10 dimensions. Colors = Ward clusters. Stars = candidate gaps.", fontsize=15, color="#444")
        lx = .675; yy = .80; fig.text(lx, yy + .035, "Clusters", fontsize=19, weight="bold")
        short = {"0": "Operators: MCP that change systems", "1": "Memory & stateful sessions", "2": "Lookups: read-only MCP",
                 "3": "Artifact makers: skills that write files", "4": "Developer workflow skills", "5": "Analyzers: MCP that compute",
                 "6": "Guidance skills: conventions", "7": "Coordinators: agent governance"}
        for c in range(lab.max() + 1):
            fig.text(lx, yy - .002, "●", color=PAL[c % 10], fontsize=20, va="center")
            fig.text(lx + .022, yy, f"C{c}  {short.get(str(c), cfg['cluster_names'].get(str(c), ''))} ({(lab == c).sum()})", fontsize=14.5, va="center"); yy -= .052
        yy -= .02; fig.text(lx, yy, "Candidate gaps (mirage test)", fontsize=17, weight="bold"); yy -= .05
        for v, txt in (("pass", "passes the mirage test"), ("doubtful", "doubtful"), ("fail", "false gap: already exists")):
            fig.text(lx, yy - .004, "★", color=VERDICT[v], fontsize=24, va="center"); fig.text(lx + .025, yy, txt, fontsize=14.5, va="center"); yy -= .048
        best = sc.sort_values("final_score", ascending=False).iloc[0] if len(sc) else None
        if best is not None:
            fig.text(lx, yy - .01, f"Top gap {best.id}: {best['name'].lower().replace(' server', '')}", fontsize=14.5, weight="bold", color=VERDICT["pass"])
            fig.text(lx, yy - .05, "(MCP servers that push events to the agent)", fontsize=13, color="#333")
        fig.text(.02, .035, "Sample: official MCP reference servers, MCP Registry, awesome-mcp-servers, public skill repos (Anthropic, OpenAI, vendors) and GitHub topics. Verified Oct 2026.",
                 fontsize=11.5, color="#555")
        fig.text(.02, .008, "UMAP is for drawing only; clusters and gaps are computed in the original coded space.  github.com/jmdevilleros/niche-map", fontsize=11.5, color="#555")
        os.makedirs(os.path.dirname(a.x_image) or ".", exist_ok=True); fig.savefig(a.x_image, dpi=100); plt.close()
    print(f"figures written to {a.out}; k={k}, silhouette={s:.3f}, N={N}")

if __name__ == "__main__": main()
