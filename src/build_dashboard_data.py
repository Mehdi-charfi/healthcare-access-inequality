"""Precompute the no-PII aggregates the Streamlit dashboard reads.

The raw doctor CSV carries phone/email PII and is gitignored, so the deployed
app must NOT read it. This script distills the raw data into small, committed,
PII-free aggregates under data/processed/:

    governorate_metrics.csv   per-gov supply/demand/gap (all specialties)
    specialty_metrics.csv     national supply vs search demand, per specialty
    specialty_gov_counts.csv  doctor counts per specialty x governorate
    governorates.geojson      boundaries keyed by our gouvernoratSlug

Run from the project root (after the raw exports + population script):

    python src/build_dashboard_data.py
"""
import unicodedata
from pathlib import Path
import pandas as pd
import geopandas as gpd

RAW, EXT, OUT = Path("data/raw"), Path("data/external"), Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

def strip_accents(s):
    return "".join(c for c in unicodedata.normalize("NFD", str(s).lower())
                   if unicodedata.category(c) != "Mn")
def norm(s):
    return "".join(ch for ch in strip_accents(s) if ch.isalnum())

docs = pd.read_csv(RAW / "doctors.csv")
pop  = pd.read_csv(EXT / "population_governorate.csv")
q    = pd.read_csv(RAW / "gsc_queries.csv")
q["nq"] = q["query"].map(strip_accents)

# ── governorate metrics (all specialties) ─────────────────────────────
supply = (docs.gouvernoratSlug.value_counts()
            .rename_axis("gouvernoratSlug").rename("doctors").reset_index())
gov = pop.merge(supply, on="gouvernoratSlug", how="left")
gov["doctors"] = gov.doctors.fillna(0).astype(int)
gov["per_100k"] = (gov.doctors / gov.population * 1e5).round(1)

overrides = {"benarous": ["ben arous"], "sidi-bouzid": ["sidi bouzid"],
             "kef": ["le kef", "kef"], "manouba": ["manouba", "mannouba"]}
gov_kw = {g: overrides.get(g, [g.replace("-", " ")]) for g in gov.gouvernoratSlug}
def match_gov(s):
    for g, kws in gov_kw.items():
        if any(strip_accents(k) in s for k in kws):
            return g
    return None
q["gov"] = q.nq.map(match_gov)
demand = q[q.gov.notna()].groupby("gov").impressions.sum().rename("search_impr")
gov = gov.merge(demand, left_on="gouvernoratSlug", right_index=True, how="left")
gov["search_impr"] = gov.search_impr.fillna(0).astype(int)
gov["demand_per_100k"] = (gov.search_impr / gov.population * 1e5).round(2)
gov["gap"] = (gov.demand_per_100k.rank(pct=True)
              - gov.per_100k.rank(pct=True)).round(3)
gov.to_csv(OUT / "governorate_metrics.csv", index=False)
print(f"governorate_metrics.csv: {len(gov)} rows")

# ── specialty metrics (national supply vs demand) ─────────────────────
TERM2SLUG = {
    "cardiologue": "cardiologie", "dermatologue": "dermatologie",
    "pediatre": "pediatrie", "gynecologue": "gynecologie-obstetrique",
    "ophtalmologue": "ophtalmologie", "ophtalmo": "ophtalmologie",
    "psychiatre": "psychiatrie", "neurologue": "neurologie",
    "radiologue": "imagerie-medicale", "urologue": "urologie",
    "rhumatologue": "rhumatologie", "endocrinologue": "endocrinologie",
    "generaliste": "medecine-generale", "pneumologue": "pneumologie",
    "orthopediste": "chirurgie-orthopedique", "orl": "orl",
    "gastro": "gastro-enterologie", "nephrologue": "nephrologie",
}
def spec_of(s):
    for term, slug in TERM2SLUG.items():
        if term in s:
            return slug
    return None
q["spec"] = q.nq.map(spec_of)
dem = q[q.spec.notna()].groupby("spec").impressions.sum().rename("demand_impr")
sup = docs.specialtySlug.value_counts().rename("doctors")
spec = pd.concat([sup, dem], axis=1).dropna(subset=["demand_impr"])
spec["doctors"] = spec.doctors.fillna(0).astype(int)
spec["demand_per_doctor"] = (spec.demand_impr / spec.doctors).round(2)
spec["supply_share"] = (spec.doctors / spec.doctors.sum()).round(4)
spec["demand_share"] = (spec.demand_impr / spec.demand_impr.sum()).round(4)
spec.index.name = "specialtySlug"
spec.sort_values("demand_per_doctor", ascending=False).to_csv(OUT / "specialty_metrics.csv")
print(f"specialty_metrics.csv: {len(spec)} rows")

# ── specialty x governorate counts (for the per-specialty map) ────────
sg = (docs.groupby(["gouvernoratSlug", "specialtySlug"]).size()
        .reset_index(name="doctors"))
sg.to_csv(OUT / "specialty_gov_counts.csv", index=False)
print(f"specialty_gov_counts.csv: {len(sg)} rows")

# ── boundaries keyed by our slug ──────────────────────────────────────
gdf = gpd.read_file(EXT / "tunisia_governorates.geojson")
sbn = {norm(s): s for s in gov.gouvernoratSlug}
gdf["gouvernoratSlug"] = gdf.shapeName.map(lambda n: {"elkef": "kef"}.get(norm(n)) or sbn.get(norm(n)))
assert gdf.gouvernoratSlug.notna().all(), "unmatched governorate shapes"
out_geo = OUT / "governorates.geojson"
if out_geo.exists():
    out_geo.unlink()
gdf[["gouvernoratSlug", "geometry"]].to_file(out_geo, driver="GeoJSON")
print(f"governorates.geojson: {len(gdf)} features")
print("done — dashboard data is PII-free and ready to commit")
