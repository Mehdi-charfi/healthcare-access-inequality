"""Tunisia population by governorate — official INS census, keyed to our slugs.

Source: Institut National de la Statistique (INS), Recensement Général de la
Population et de l'Habitat (RGPH) 2014 — the last full census with per-
governorate counts. Total ≈ 10.98 M, matching the national 2014 figure.

We embed the table in code (rather than scraping INS) so the lineage is
committed and reproducible. Run from the project root:

    python src/population_tn.py     # -> data/external/population_governorate.csv
"""
import csv
from pathlib import Path

# slug -> (display name, 2014 census population)
POPULATION = {
    "tunis":      ("Tunis",       1056247),
    "ariana":     ("Ariana",       576088),
    "benarous":   ("Ben Arous",    631842),
    "manouba":    ("Manouba",      379518),
    "nabeul":     ("Nabeul",       787920),
    "zaghouan":   ("Zaghouan",     176945),
    "bizerte":    ("Bizerte",      568219),
    "beja":       ("Béja",         303032),
    "jendouba":   ("Jendouba",     401477),
    "kef":        ("Le Kef",       243156),
    "siliana":    ("Siliana",      223087),
    "kairouan":   ("Kairouan",     570559),
    "kasserine":  ("Kasserine",    439243),
    "sidi-bouzid": ("Sidi Bouzid", 429912),  # hyphenated to match the doctor data's slug
    "sousse":     ("Sousse",       674971),
    "monastir":   ("Monastir",     548828),
    "mahdia":     ("Mahdia",       410812),
    "sfax":       ("Sfax",         955421),
    "gafsa":      ("Gafsa",        337331),
    "tozeur":     ("Tozeur",       107912),
    "kebili":     ("Kébili",       156961),
    "gabes":      ("Gabès",        374300),
    "medenine":   ("Médenine",     479520),
    "tataouine":  ("Tataouine",    149453),
}

if __name__ == "__main__":
    out = Path("data/external/population_governorate.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["gouvernoratSlug", "governorate", "population"])
        for slug, (name, pop) in POPULATION.items():
            w.writerow([slug, name, pop])
    total = sum(p for _, p in POPULATION.values())
    print(f"wrote {out}: {len(POPULATION)} governorates, total pop {total:,}")
