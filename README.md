# Tunisia Medical Access — Supply vs Demand

> A data-science portfolio project: mapping **healthcare access inequality** in
> Tunisia by joining the *supply* of doctors against the public *search demand*
> for them.

Most "find a doctor" analyses stop at counting doctors. The interesting
question is the **gap**:

> **Where is search demand for a specialty high, but doctor supply low?**

That gap — demand the local supply can't meet — is a data-driven definition of
a *medical desert*, and it's the headline of this project.

## The two datasets

| Side | File | What it is | Rows |
|---|---|---|---|
| **Supply** | `data/raw/doctors.csv` | Every practising doctor in the [CNOM](https://www.ordre-medecins.org.tn/) national registry (via [medline.tn](https://medline.tn)) — specialty, governorate, delegation, address, geocode | **9,851** |
| **Demand** | `data/raw/gsc_*.csv` | 16 months of Google Search Console — the queries people typed to reach medline.tn, with clicks / impressions / position | ~7,900 queries |

48 specialties · 24 governorates · 228 delegations. Real-world messiness
included: 26% of doctors have no geocode, 10% no email, free-text bilingual
(French/Arabic) addresses.

### Data dictionary — `doctors.csv`

| Column | Notes |
|---|---|
| `slug`, `name`, `firstName`, `lastName` | identity |
| `nameAr` | Arabic-script name (~9% coverage) |
| `specialtySlug` | one of 48 specialties |
| `gouvernoratSlug` | governorate from the resolved location |
| `delegationGov`, `delegationSlug` | delegation from the address postal code |
| `address` | free-text cabinet address |
| `phone`, `email` | **PII — gitignored, local only** |
| `mapQuery` | `place_id:…` or `lat,lng` geocode (`""` = none) |

## Project roadmap

1. **Supply** — clean, profile, density per governorate/delegation
2. **Per-capita** — join INS population → doctors per 100k (raw counts lie)
3. **Demand** — parse GSC queries → specialty × city intent
4. **The gap** — merge demand onto supply → desert score + choropleth map
5. **Deploy** — Streamlit dashboard (filter by specialty/region)

See `notebooks/01_supply_demand_eda.ipynb` for the starting point.

## Reproduce

```bash
# 1. Python env
python -m venv .venv && .venv\Scripts\activate    # Windows
pip install -r requirements.txt

# 2. (Re)generate the raw data — needs the medline repo + the ~/.gsc tool
node src/export_doctors.mjs     # -> data/raw/doctors.csv
node src/export_gsc.mjs         # -> data/raw/gsc_*.csv

# 3. Download external data (see data/external/README.md)
#    population_governorate.csv  +  tunisia_governorates.geojson

# 4. Explore
jupyter lab
```

## Responsible-data note

The doctor directory is built from a **public** registry, but the raw export
still contains personal phone numbers and emails. Those columns are
**gitignored** and never leave the local machine — only no-PII aggregates
(counts per specialty/region) are committed. The analysis needs none of the PII.

## Credits

Supply data: Conseil National de l'Ordre des Médecins de Tunisie, surfaced via
[medline.tn](https://medline.tn). Demand data: Google Search Console.
