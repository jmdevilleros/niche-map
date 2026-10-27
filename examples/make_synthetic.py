#!/usr/bin/env python3
"""Generate the SYNTHETIC example dataset (fictional indoor-plant-care products).
Every item, name and number is invented. Links point to the reserved example.invalid domain.
The generator builds clusters around a few archetypes and leaves some combinations deliberately empty,
so the pipeline has something to find. Run: python make_synthetic.py  ->  synthetic_items.csv"""
import os
import numpy as np, pandas as pd

rng = np.random.default_rng(20261026)
SYL = ["leaf", "moss", "fern", "root", "sprout", "bloom", "petal", "stem", "terra", "verd", "dew", "bud", "ivy", "loam", "frond"]
SUF = ["ly", "io", "wise", "kit", "mate", "nest", "pal", "lab", "hub", "box"]

# archetypes: (form, job, trigger, user, setting, price, automation, upkeep, weight)
ARCH = [
    ("device",     "water",     "sensor",   "beginner", "windowsill", 1, 2, 1, 9),
    ("device",     "light",     "schedule", "hobbyist", "shelf",      1, 2, 0, 8),
    ("app",        "diagnose",  "manual",   "beginner", "windowsill", 0, 1, 0, 9),
    ("app",        "water",     "schedule", "beginner", "shelf",      0, 1, 0, 6),
    ("consumable", "feed",      "manual",   "hobbyist", "shelf",      0, 0, 1, 8),
    ("consumable", "feed",      "schedule", "beginner", "windowsill", 0, 0, 1, 5),
    ("kit",        "propagate", "manual",   "hobbyist", "shelf",      1, 0, 2, 7),
    ("service",    "decorate",  "manual",   "pro",      "office",     2, 0, 0, 6),
    ("service",    "water",     "schedule", "pro",      "office",     2, 1, 0, 5),
    ("device",     "diagnose",  "sensor",   "hobbyist", "balcony",    1, 2, 1, 4),
]
VALUES = {"form": ["device", "app", "consumable", "kit", "service"],
          "job": ["water", "light", "feed", "diagnose", "propagate", "decorate"],
          "trigger": ["manual", "schedule", "sensor"],
          "user": ["beginner", "hobbyist", "pro"],
          "setting": ["windowsill", "shelf", "balcony", "office"]}

rows, used = [], set()
def name():
    while True:
        n = rng.choice(SYL).capitalize() + rng.choice(SUF)
        if n not in used: used.add(n); return n

for form, job, trig, user, sett, price, auto, upkeep, w in ARCH:
    for _ in range(w):
        r = dict(form=form, job=job, trigger=trig, user=user, setting=sett, price_tier=price, automation=auto, upkeep=upkeep)
        # small jitter so clusters are not perfectly pure
        if rng.random() < 0.45: r["setting"] = str(rng.choice(["windowsill", "shelf", "balcony"]))
        if rng.random() < 0.40: r["user"] = str(rng.choice(["beginner", "hobbyist"])) if user != "pro" else "pro"
        if rng.random() < 0.20: r["job"] = str(rng.choice(["water", "light", "feed", "diagnose"]))
        if rng.random() < 0.20 and form in ("device", "app"): r["trigger"] = str(rng.choice(["manual", "schedule", "sensor"]))
        if rng.random() < 0.40: r["price_tier"] = int(np.clip(price + rng.choice([-1, 1]), 0, 2))
        if rng.random() < 0.40: r["upkeep"] = int(np.clip(upkeep + rng.choice([-1, 1]), 0, 2))
        if rng.random() < 0.25 and form != "service": r["automation"] = int(np.clip(auto + rng.choice([-1, 1]), 0, 2))
        if r["form"] == "service": r["automation"] = min(r["automation"], 1)
        if r["trigger"] == "sensor": r["automation"] = 2
        if r["job"] == "decorate" and r["form"] == "consumable": r["job"] = "feed"
        n = name(); r = {"name": n, **r}
        r["link"] = f"https://{n.lower()}.example.invalid/"
        r["reviews_synthetic"] = int(rng.lognormal(4, 1.1))
        rows.append(r)

df = pd.DataFrame(rows)
df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "synthetic_items.csv"), index=False)
print(f"{len(df)} synthetic items written to synthetic_items.csv")
for c in VALUES: print(c, df[c].value_counts().to_dict())
