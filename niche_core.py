#!/usr/bin/env python3
"""
niche_core.py - Niche map in a conceptual space (generic, any domain).

Input:
  1) CSV of items x dimensions (one row per real item; columns = coded dimensions)
  2) JSON config declaring the dimensions, their scales, weights, coherence rules and (optional) candidate niches.

Output (in --out):
  clusters.csv, cluster_profiles.md, silhouette.csv, pca_loadings.csv, triple_gaps.csv,
  density_gaps.csv, density_gaps_top.csv, candidate_neighbors.csv, supply_demand_clusters.csv,
  fig_umap.png, fig_pca.png, fig_heatmaps.png, fig_gaps.png, summary.json

Usage:
  python niche_core.py --items items.csv --config config.json --out out/ [--samples 400000]
  python niche_core.py --items items.csv --config config.json --out out/ --compare reference.csv

Config format (minimal example):
{
 "id_col": "name",
 "categorical": {"gesture": {"values": ["T","S","D"], "weight": 1.0, "labels": {"T":"tap"}}},
 "ordinal": {"time_pressure": [0,2], "avatar": [0,1]},
 "gap_dims": ["gesture","time_pressure", "..."],          # dimensions used in the triple search (concept dimensions)
 "rules": [[["goal","==","Z"],["time_pressure","==",2]]],  # FORBIDDEN combinations (all conditions at once)
 "anchor_dims": ["verb","goal"],                           # optional: every gap triple must include >=1 of these (avoids "meta" gaps)
 "target_filter": [["complexity","<=",1]],                 # optional: conditions every density gap must satisfy (user fit)
 "k_range": [5,10], "seed": 42, "umap_neighbors": 12,
 "min_pair_support": 2, "min_expected": 1.2, "max_observed": 1,
 "heatmap_pairs": [["verb","gesture"]],
 "label_items": ["Item A"],
 "candidates": [{"id":"N1","name":"Spin","vec":{"gesture":"R","time_pressure":2}}],
 "demand_cols": ["reviews"],                               # optional: demand signal per cluster vs supply
 "cluster_names": {"0": "human-readable cluster name"}     # optional: filled in after reading cluster_profiles.md
}
Rule operators: ==, !=, in, not_in, >=, <=.
"""
import argparse, itertools, json, os, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")

CFG_ORD = set()

# ---------------------------------------------------------------- loading and encoding
def load(items_path, cfg_path):
    df = pd.read_csv(items_path)
    with open(cfg_path, encoding="utf-8") as f:
        cfg = json.load(f)
    cfg.setdefault("ordinal", {}); cfg.setdefault("rules", []); cfg.setdefault("candidates", [])
    cfg.setdefault("k_range", [4, 10]); cfg.setdefault("seed", 42); cfg.setdefault("umap_neighbors", 12)
    cfg.setdefault("min_pair_support", 2); cfg.setdefault("min_expected", 1.2); cfg.setdefault("max_observed", 1)
    cfg.setdefault("gap_dims", list(cfg["categorical"]) + list(cfg["ordinal"]))
    for c, spec in cfg["categorical"].items():
        if c not in df: raise ValueError(f"Dimension {c} missing from the items CSV")
        df[c] = df[c].astype(str)
        spec["values"] = [str(v) for v in spec["values"]]
        bad = set(df[c]) - set(spec["values"])
        if bad: raise ValueError(f"Dimension {c}: values outside the scale {bad}")
    for c, (lo, hi) in cfg["ordinal"].items():
        if c not in df: raise ValueError(f"Ordinal dimension {c} missing from the items CSV")
        if df[c].isna().any() or (df[c] < lo).any() or (df[c] > hi).any():
            raise ValueError(f"Ordinal dimension {c} out of range [{lo},{hi}] or empty")
    small = {c: [v for v, n in df[c].value_counts().items() if n < 2] for c in cfg["categorical"]}
    small = {c: v for c, v in small.items() if v}
    if small: print(f"WARNING: categories with <2 items (merge or drop them, see SKILL.md step 2): {small}")
    return df, cfg

def encode(d, cfg):
    """Weighted one-hot (weight/sqrt(2), so switching category costs the same as an end-to-end ordinal move) + ordinal scaled to 0-1."""
    parts = []
    for c, spec in cfg["categorical"].items():
        w = spec.get("weight", 1.0) / np.sqrt(2)
        col = d[c].astype(str).values
        parts.append(np.array([[1.0 if x == v else 0.0 for v in spec["values"]] for x in col]) * w)
    for c, (lo, hi) in cfg["ordinal"].items():
        parts.append(((d[c].astype(float).values - lo) / (hi - lo))[:, None] * cfg.get("ordinal_weights", {}).get(c, 1.0))
    return np.hstack(parts)

def feature_names(cfg):
    return [f"{c}={v}" for c, s in cfg["categorical"].items() for v in s["values"]] + list(cfg["ordinal"])

# ---------------------------------------------------------------- coherence rules
def _cond(row, dim, op, val):
    x = row[dim]
    num = dim in CFG_ORD
    x = float(x) if num else str(x)
    cast = (lambda v: float(v)) if num else (lambda v: str(v))
    if op == "==": return x == cast(val)
    if op == "!=": return x != cast(val)
    if op == "in": return x in [cast(v) for v in val]
    if op == "not_in": return x not in [cast(v) for v in val]
    if op == ">=": return float(x) >= float(val)
    if op == "<=": return float(x) <= float(val)
    raise ValueError(f"Unknown operator {op}")

def incoherent(row, rules):
    return any(all(_cond(row, *c) for c in rule) for rule in rules)

def incoherent_partial(row, rules):
    """A triple is incoherent if some rule is fully determined by its 3 values and holds."""
    for rule in rules:
        if all(c[0] in row for c in rule) and all(_cond(row, *c) for c in rule): return True
    return False

# ---------------------------------------------------------------- analysis
def clusters(X, cfg):
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    rows, best = [], None
    for k in range(cfg["k_range"][0], cfg["k_range"][1] + 1):
        lab = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(X)
        s = silhouette_score(X, lab); rows.append((k, round(s, 4)))
        if best is None or s > best[0] + 0.005: best = (s, k, lab)   # a larger k must beat the best by >0.005
    return best, pd.DataFrame(rows, columns=["k", "silhouette"])

def triple_gaps(df, cfg):
    dims, N, res = cfg["gap_dims"], len(df), []
    S = df[dims].astype(str)
    anchors = set(cfg.get("anchor_dims", []))
    for a, b, c in itertools.combinations(dims, 3):
        if anchors and not anchors & {a, b, c}: continue   # each triple must touch >=1 anchor (concept) dimension
        pa, pb, pc = [S[x].value_counts(normalize=True) for x in (a, b, c)]
        obs = S.groupby([a, b, c]).size()
        pab, pac, pbc = S.groupby([a, b]).size(), S.groupby([a, c]).size(), S.groupby([b, c]).size()
        for va, vb, vc in itertools.product(pa.index, pb.index, pc.index):
            o = obs.get((va, vb, vc), 0)
            if min(pab.get((va, vb), 0), pac.get((va, vc), 0), pbc.get((vb, vc), 0)) < cfg["min_pair_support"]: continue
            e = N * pa[va] * pb[vb] * pc[vc]
            if o <= cfg["max_observed"] and e >= cfg["min_expected"]:
                row = {a: va, b: vb, c: vc}
                res.append((a, va, b, vb, c, vc, o, round(e, 2), round((e - o) / np.sqrt(e), 2), not incoherent_partial(row, cfg["rules"])))
    g = pd.DataFrame(res, columns=["d1", "v1", "d2", "v2", "d3", "v3", "observed", "expected", "z", "coherent"])
    return g.sort_values("z", ascending=False).reset_index(drop=True)

def density_gaps(df, X, cfg, samples, rng):
    dims = list(cfg["categorical"]) + list(cfg["ordinal"])
    pairs = list(itertools.combinations(dims, 2))
    seen = {(a, b): set(zip(df[a].astype(str), df[b].astype(str))) for a, b in pairs}
    S = {c: rng.choice(s["values"], samples) for c, s in cfg["categorical"].items()}
    for c, (lo, hi) in cfg["ordinal"].items(): S[c] = rng.integers(lo, hi + 1, samples)
    S = pd.DataFrame(S).drop_duplicates()
    # 1) every pair of values must exist in >=1 real item (recombination of known pieces)
    mask = np.ones(len(S), bool)
    for a, b in pairs:
        key = pd.Series(list(zip(S[a].astype(str), S[b].astype(str))), index=S.index)
        mask &= key.isin(seen[(a, b)]).values
    S = S[mask]
    # 2) coherence rules
    S = S[[not incoherent(r, cfg["rules"]) for _, r in S.iterrows()]].copy()
    # 3) target-user filter (e.g. complexity<=1, self_serve==1): only gaps THIS user could build/sell
    tf = cfg.get("target_filter", [])
    if tf and len(S): S = S[[all(_cond(r, *c) for c in tf) for _, r in S.iterrows()]].copy()
    if S.empty: return S
    from sklearn.neighbors import NearestNeighbors
    nn = NearestNeighbors(n_neighbors=min(3, len(X))).fit(X)
    dist, idx = nn.kneighbors(encode(S, cfg))
    S["dist_min"] = dist[:, 0].round(3)
    S["neighbors"] = [", ".join(df[cfg["id_col"]].astype(str).iloc[i]) for i in idx]
    return S.sort_values("dist_min", ascending=False)

# ---------------------------------------------------------------- figures
def figs(df, X, U, P, pca, lab, cfg, out, UC=None, PC=None, cands=None, gaps=None):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    from scipy.stats import gaussian_kde
    pal = plt.get_cmap("tab10" if lab.max() < 10 else "tab20")
    names = cfg.get("cluster_names", {})
    # UMAP + density
    fig, ax = plt.subplots(figsize=(10, 7))
    kd = gaussian_kde(U.T, bw_method=.25)
    gx, gy = np.mgrid[U[:, 0].min()-1:U[:, 0].max()+1:200j, U[:, 1].min()-1:U[:, 1].max()+1:200j]
    z = kd(np.vstack([gx.ravel(), gy.ravel()])).reshape(gx.shape)
    ax.contourf(gx, gy, z, levels=8, cmap="Greys", alpha=.35)
    for c in range(lab.max() + 1):
        m = lab == c
        ax.scatter(U[m, 0], U[m, 1], s=36, color=pal(c), edgecolor="white", lw=.5, label=f"C{c} {names.get(str(c), '')}")
    for i, n in enumerate(df[cfg["id_col"]]):
        if n in cfg.get("label_items", []): ax.annotate(n, U[i], fontsize=7, xytext=(3, 3), textcoords="offset points")
    if UC is not None:
        ax.scatter(UC[:, 0], UC[:, 1], marker="*", s=240, color="#111", edgecolor="#ffd400", zorder=5, label="candidates")
        offs = [(8, -10), (8, 8), (-22, 8), (-22, -12), (10, 0), (-26, 0)]   # simple rotation of label offsets to reduce overlap
        for i, c in enumerate(cands): ax.annotate(c["id"], UC[i], fontsize=8, xytext=offs[i % len(offs)], textcoords="offset points",
                                                  arrowprops=dict(arrowstyle="-", lw=.4, color="#555"))
    ax.set_xticks([]); ax.set_yticks([]); ax.legend(fontsize=7, loc="center left", bbox_to_anchor=(1, .5), frameon=False)
    ax.set_title("UMAP (visualization only) · color = cluster · grey = density", loc="left")
    fig.tight_layout(); fig.savefig(f"{out}/fig_umap.png", dpi=160); plt.close()
    # PCA biplot
    ld = pd.DataFrame(pca.components_[:2].T, index=feature_names(cfg), columns=["a", "b"])
    top = ld.assign(n=np.hypot(ld.a, ld.b)).sort_values("n", ascending=False).head(12)
    fig, ax = plt.subplots(figsize=(10, 7))
    for c in range(lab.max() + 1):
        m = lab == c; ax.scatter(P[m, 0], P[m, 1], s=28, color=pal(c), alpha=.7, label=f"C{c}")
    for k_, r in top.iterrows():
        ax.arrow(0, 0, r.a*2.2, r.b*2.2, color="#c0392b", width=.004, head_width=.04, alpha=.8)
        ax.text(r.a*2.45, r.b*2.45, k_, color="#c0392b", fontsize=7, ha="center")
    if PC is not None:
        ax.scatter(PC[:, 0], PC[:, 1], marker="*", s=200, color="#111", edgecolor="#ffd400", zorder=5)
        for i, c in enumerate(cands): ax.annotate(c["id"], PC[i, :2], fontsize=7, xytext=(5, 4), textcoords="offset points")
    ev = pca.explained_variance_ratio_
    ax.set_xlabel(f"PC1 ({ev[0]*100:.0f} %)"); ax.set_ylabel(f"PC2 ({ev[1]*100:.0f} %)")
    ax.set_title("PCA biplot: arrows = highest-loading features (gradients)", loc="left"); ax.legend(fontsize=7, ncol=5, frameon=False)
    fig.tight_layout(); fig.savefig(f"{out}/fig_pca.png", dpi=160); plt.close()
    # pairwise heatmaps
    hp = cfg.get("heatmap_pairs", [])[:4]
    if hp:
        n = len(hp); fig, axs = plt.subplots(1 if n == 1 else 2, 1 if n == 1 else 2, figsize=(11, 9.5 if n > 1 else 5))
        axs = np.atleast_1d(axs).ravel()
        for ax, (a, b) in zip(axs, hp):
            ia = cfg["categorical"][a]["values"] if a in cfg["categorical"] else sorted(df[a].unique())
            ib = cfg["categorical"][b]["values"] if b in cfg["categorical"] else sorted(df[b].unique())
            t = pd.crosstab(df[a], df[b]).reindex(index=ia, columns=ib, fill_value=0)
            ax.imshow(t.values, cmap="magma_r", aspect="auto", vmin=0, vmax=max(6, t.values.max()))
            la = cfg["categorical"].get(a, {}).get("labels", {}); lb = cfg["categorical"].get(b, {}).get("labels", {})
            ax.set_xticks(range(len(ib)), [lb.get(str(v), str(v)) for v in ib], rotation=40, ha="right", fontsize=8)
            ax.set_yticks(range(len(ia)), [la.get(str(v), str(v)) for v in ia], fontsize=8)
            for i in range(t.shape[0]):
                for j in range(t.shape[1]):
                    v = t.values[i, j]; ax.text(j, i, v if v else "·", ha="center", va="center", fontsize=7, color="white" if v >= 4 else "#555")
            ax.set_title(f"{a} × {b}")
        for ax in axs[len(hp):]: ax.axis("off")
        fig.tight_layout(); fig.savefig(f"{out}/fig_heatmaps.png", dpi=150); plt.close()
    # triple gaps
    if gaps is not None and len(gaps):
        g = gaps[gaps.coherent].head(15)
        fig, ax = plt.subplots(figsize=(10, 6)); y = np.arange(len(g))[::-1]
        ax.barh(y, g.expected, color="#d9d9e8", label="expected (independence)"); ax.barh(y, g.observed, color="#c0392b", label="observed")
        ax.set_yticks(y, [f"{r.d1}={r.v1} + {r.d2}={r.v2} + {r.d3}={r.v3}" for r in g.itertuples()], fontsize=7)
        ax.legend(frameon=False, fontsize=8); ax.set_title("Top 15 coherent absent triples", loc="left")
        fig.tight_layout(); fig.savefig(f"{out}/fig_gaps.png", dpi=160); plt.close()

# ---------------------------------------------------------------- main
def main():
    global CFG_ORD
    ap = argparse.ArgumentParser(description="Niche map: clusters, gradients and gaps in a coded conceptual space.")
    ap.add_argument("--items", required=True, help="CSV with one row per item and one column per dimension")
    ap.add_argument("--config", required=True, help="JSON config (format in this file's header)")
    ap.add_argument("--out", required=True, help="output folder")
    ap.add_argument("--samples", type=int, default=400000, help="random synthetic vectors for density gaps (default 400000)")
    ap.add_argument("--compare", help="reference CSV with id column and a 'cluster' column, to report ARI")
    ap.add_argument("--no-figs", action="store_true", help="skip figures")
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    df, cfg = load(a.items, a.config); CFG_ORD = set(cfg["ordinal"])
    rng = np.random.default_rng(cfg["seed"])
    X = encode(df, cfg)
    from sklearn.decomposition import PCA
    from sklearn.neighbors import NearestNeighbors
    import umap
    pca = PCA(n_components=min(6, X.shape[1]), random_state=0).fit(X); P = pca.transform(X)
    um = umap.UMAP(n_neighbors=min(cfg["umap_neighbors"], len(df) - 1), min_dist=.25, random_state=cfg["seed"]).fit(X); U = um.embedding_
    (s, k, lab), sil = clusters(X, cfg); df["cluster"] = lab
    sil.to_csv(f"{a.out}/silhouette.csv", index=False)
    k_edge = k in (cfg["k_range"][0], cfg["k_range"][1])
    if k_edge: print(f"WARNING: best k ({k}) is on the edge of k_range {cfg['k_range']}; widen k_range or justify k by interpretability.")
    small = int((pd.Series(lab).value_counts() < 3).sum())
    if small: print(f"WARNING: {small} cluster(s) with <3 items; likely artifacts or very thin niches.")
    df.to_csv(f"{a.out}/clusters.csv", index=False)
    # cluster profiles (to name clusters by hand)
    with open(f"{a.out}/cluster_profiles.md", "w", encoding="utf-8") as f:
        for c in range(k):
            m = df[df.cluster == c]
            f.write(f"## C{c} ({len(m)})\n{', '.join(m[cfg['id_col']].astype(str))}\n\n")
            for col in list(cfg["categorical"]) + list(cfg["ordinal"]):
                f.write(f"- {col}: {m[col].value_counts().head(3).to_dict()}\n")
            f.write("\n")
    # supply vs demand per cluster (optional): numeric demand-signal columns (reviews, installs, searches, stars...)
    if cfg.get("demand_cols"):
        rows_ = []
        for c in range(k):
            m = df[df.cluster == c]; r_ = {"cluster": c, "cluster_name": cfg.get("cluster_names", {}).get(str(c), ""), "supply_n": len(m)}
            for dc in cfg["demand_cols"]:
                v = pd.to_numeric(m[dc], errors="coerce")
                r_[f"{dc}_median"] = None if v.notna().sum() == 0 else float(v.median()); r_[f"{dc}_coverage"] = round(v.notna().mean(), 2)
            rows_.append(r_)
        pd.DataFrame(rows_).to_csv(f"{a.out}/supply_demand_clusters.csv", index=False)
    ld = pd.DataFrame(pca.components_[:3].T, index=feature_names(cfg), columns=["PC1", "PC2", "PC3"]); ld.to_csv(f"{a.out}/pca_loadings.csv")
    gaps = triple_gaps(df, cfg); gaps.to_csv(f"{a.out}/triple_gaps.csv", index=False)
    dens = density_gaps(df, X, cfg, a.samples, rng); dens.to_csv(f"{a.out}/density_gaps.csv", index=False)
    keydims = cfg.get("density_dedupe", list(cfg["categorical"])[:4])
    (dens.drop_duplicates(subset=keydims).head(40) if len(dens) else dens).to_csv(f"{a.out}/density_gaps_top.csv", index=False)
    dgg, _ = NearestNeighbors(n_neighbors=2).fit(X).kneighbors(X); nnd = dgg[:, 1]
    n_dup = int((nnd == 0).sum())
    if n_dup: print(f"WARNING: {n_dup} item(s) share an identical vector with another item; the rubric may be too coarse to tell them apart.")
    med = float(np.median(nnd[nnd > 0])) if (nnd > 0).any() else 0.0   # reference scale: median distance to nearest DISTINCT real item
    UC = PC = None; cands = cfg["candidates"]
    if cands:
        CV = pd.DataFrame([c["vec"] for c in cands]); XC = encode(CV, cfg)
        dc, ic = NearestNeighbors(n_neighbors=min(3, len(X))).fit(X).kneighbors(XC)
        UC, PC = um.transform(XC), pca.transform(XC)   # UMAP.transform pulls new points toward existing islands: read novelty from dist_min, not the plot
        pd.DataFrame({"id": [c["id"] for c in cands], "name": [c.get("name", "") for c in cands], "dist_min": dc[:, 0].round(3),
                      "dist_rel_median": (dc[:, 0] / med).round(2) if med > 0 else np.nan,
                      "neighbors": [", ".join(df[cfg["id_col"]].astype(str).iloc[i]) for i in ic],
                      "incoherent": [incoherent(r, cfg["rules"]) for _, r in CV.iterrows()]}).to_csv(f"{a.out}/candidate_neighbors.csv", index=False)
    if not a.no_figs: figs(df, X, U, P, pca, lab, cfg, a.out, UC, PC, cands, gaps)
    res = {"n_items": len(df), "n_features": X.shape[1], "k": int(k), "silhouette": round(float(s), 3),
           "pca_variance": [round(float(v), 3) for v in pca.explained_variance_ratio_[:3]], "median_nn_distance": round(med, 3), "items_with_identical_vector": n_dup,
           "gap_triples": int(len(gaps)), "coherent_gap_triples": int(gaps.coherent.sum()) if len(gaps) else 0,
           "feasible_synthetic_vectors": int(len(dens)), "k_on_edge": bool(k_edge),
           "silhouette_by_k": dict(zip(sil.k.astype(str), sil.silhouette))}
    if a.compare:
        from sklearn.metrics import adjusted_rand_score
        ref = pd.read_csv(a.compare).set_index(cfg["id_col"])["cluster"]
        res["ARI_vs_reference"] = round(float(adjusted_rand_score(ref.loc[df[cfg["id_col"]]].values, lab)), 3)
    with open(f"{a.out}/summary.json", "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1, ensure_ascii=False)
    print(json.dumps(res, ensure_ascii=False, indent=1))

if __name__ == "__main__": main()
