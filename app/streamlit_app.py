"""Tunisia — Private Healthcare Access dashboard.

Interactive view of private-practice (cabinet) doctor SUPPLY vs Google search
DEMAND across Tunisia's 24 governorates and ~48 specialties. Reads only the
PII-free aggregates in data/processed/ (built by src/build_dashboard_data.py),
so it is safe to deploy publicly.

Run locally:   streamlit run app/streamlit_app.py
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DATA = Path(__file__).resolve().parent.parent / "data" / "processed"

PRETTY = {
    "medecine-generale": "Médecine générale", "gynecologie-obstetrique": "Gynécologie-obstétrique",
    "pediatrie": "Pédiatrie", "ophtalmologie": "Ophtalmologie", "imagerie-medicale": "Imagerie médicale",
    "cardiologie": "Cardiologie", "chirurgie-orthopedique": "Chirurgie orthopédique", "orl": "ORL",
    "dermatologie": "Dermatologie", "chirurgie-generale": "Chirurgie générale",
    "anesthesie-reanimation": "Anesthésie-réanimation", "gastro-enterologie": "Gastro-entérologie",
    "psychiatrie": "Psychiatrie", "pneumologie": "Pneumologie", "biologie-medicale": "Biologie médicale",
    "urologie": "Urologie", "endocrinologie": "Endocrinologie", "neurologie": "Neurologie",
    "rhumatologie": "Rhumatologie", "nephrologie": "Néphrologie", "stomatologie": "Stomatologie",
}
def pretty(slug: str) -> str:
    return PRETTY.get(slug, slug.replace("-", " ").title())


@st.cache_data
def load():
    gov = pd.read_csv(DATA / "governorate_metrics.csv")
    spec = pd.read_csv(DATA / "specialty_metrics.csv")
    sg = pd.read_csv(DATA / "specialty_gov_counts.csv")
    geo = json.loads((DATA / "governorates.geojson").read_text(encoding="utf-8"))
    return gov, spec, sg, geo


st.set_page_config(page_title="Tunisia · Private Healthcare Access", layout="wide",
                   page_icon="🩺")
gov, spec, sg, geo = load()

st.title("🩺 Tunisia — Private Healthcare Access")
st.caption("Private-practice (cabinet) doctor **supply** vs Google Search **demand**, "
           "by governorate and specialty. Supply ÷ INS 2014 census = doctors per 100k.")

with st.expander("Scope & caveats — read me"):
    st.markdown(
        "- **Private practice only.** These are doctors listed at their own *cabinet*; "
        "doctors working solely in **public hospitals are not counted**. Low scores in the "
        "interior partly reflect where private practice is viable, not total care.\n"
        "- **Demand = Google Search Console** impressions reaching medline.tn (~16 months). "
        "It is a directional *signal*, supply-confounded and modest in volume — not a demand census.\n"
        "- Source: CNOM registry via [medline.tn](https://medline.tn); population: INS RGPH 2014."
    )

# ── Sidebar controls ──────────────────────────────────────────────────
spec_slugs = sorted(sg.specialtySlug.unique(), key=pretty)
choice = st.sidebar.selectbox(
    "Specialty", ["All specialties"] + spec_slugs,
    format_func=lambda s: s if s == "All specialties" else pretty(s),
)
is_all = choice == "All specialties"

metric_options = ["Doctors per 100k"] + (["Supply–demand gap"] if is_all else [])
metric = st.sidebar.radio("Map metric", metric_options)
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"**{int(gov.doctors.sum()):,}** private-practice doctors  \n"
    f"**{gov.shape[0]}** governorates · **{len(spec_slugs)}** specialties"
)

# ── Build the map dataframe for the current selection ─────────────────
if is_all:
    mdf = gov.copy()
else:
    counts = (sg[sg.specialtySlug == choice][["gouvernoratSlug", "doctors"]]
              .set_index("gouvernoratSlug").doctors)
    mdf = gov[["gouvernoratSlug", "governorate", "population"]].copy()
    mdf["doctors"] = mdf.gouvernoratSlug.map(counts).fillna(0).astype(int)
    mdf["per_100k"] = (mdf.doctors / mdf.population * 1e5).round(1)

if metric == "Supply–demand gap":
    color_col, cmap, title = "gap", "RdBu_r", "Supply–demand gap (red = underserved)"
    crange = [-mdf.gap.abs().max(), mdf.gap.abs().max()]
else:
    color_col, cmap, crange = "per_100k", "RdYlGn", None
    title = f"{'All specialties' if is_all else pretty(choice)} — doctors per 100k"

# ── KPIs ──────────────────────────────────────────────────────────────
nat = round(mdf.doctors.sum() / mdf.population.sum() * 1e5, 1)
worst = mdf.sort_values("per_100k").iloc[0]
best = mdf.sort_values("per_100k").iloc[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Doctors (selection)", f"{int(mdf.doctors.sum()):,}")
c2.metric("National density", f"{nat} / 100k")
c3.metric("Best served", f"{best.governorate}", f"{best.per_100k:.0f} / 100k")
c4.metric("Least served", f"{worst.governorate}", f"{worst.per_100k:.0f} / 100k",
          delta_color="inverse")

# ── Map + ranked table ────────────────────────────────────────────────
left, right = st.columns([3, 2])
with left:
    # choropleth_map (maplibre + free carto tiles, no token) renders custom
    # geojson reliably — unlike px.choropleth + fitbounds, which collapsed the
    # polygons into a bounding rectangle.
    fig = px.choropleth_map(
        mdf, geojson=geo, locations="gouvernoratSlug",
        featureidkey="properties.gouvernoratSlug",
        color=color_col, color_continuous_scale=cmap,
        range_color=crange, hover_name="governorate",
        hover_data={"gouvernoratSlug": False, "doctors": True, "per_100k": True},
        map_style="carto-positron", center={"lat": 34.0, "lon": 9.5},
        zoom=4.7, opacity=0.75,
    )
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), title=title, height=520)
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.markdown("**Governorate ranking**")
    cols = ["governorate", "doctors", "per_100k"] + (["gap"] if metric == "Supply–demand gap" else [])
    table = mdf.sort_values(color_col, ascending=(metric == "Supply–demand gap"))[cols]
    st.dataframe(table.reset_index(drop=True), use_container_width=True, height=470,
                 hide_index=True)

# ── Specialty supply vs demand ────────────────────────────────────────
st.markdown("---")
st.subheader("Which specialties are over-demanded?")
st.caption("Search-demand share vs doctor-supply share. Above the dashed line = more "
           "search interest than its share of doctors → under-supplied.")
sp = spec.copy()
sp["label"] = sp.specialtySlug.map(pretty)
sp["highlight"] = "Other" if is_all else "Other"
if not is_all and choice in set(sp.specialtySlug):
    sp.loc[sp.specialtySlug == choice, "highlight"] = "Selected"
lim = max(sp.supply_share.max(), sp.demand_share.max()) * 1.1
fig2 = px.scatter(
    sp, x="supply_share", y="demand_share", text="label",
    color="highlight", color_discrete_map={"Other": "#6B1D2F", "Selected": "#1a7d3c"},
    hover_data={"doctors": True, "demand_impr": True, "demand_per_doctor": True,
                "supply_share": False, "demand_share": False, "highlight": False, "label": False},
)
fig2.add_shape(type="line", x0=0, y0=0, x1=lim, y1=lim, line=dict(dash="dash", color="#bbb"))
fig2.update_traces(textposition="top center", textfont_size=9, marker_size=10)
fig2.update_layout(showlegend=False, height=560, xaxis_title="Supply share (doctors)",
                   yaxis_title="Demand share (search impressions)",
                   xaxis_range=[0, lim], yaxis_range=[0, lim],
                   margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.markdown(
    "Portfolio project · Doctor directory data from "
    "**[medline.tn](https://medline.tn)** — the independent directory of doctors "
    "in Tunisia · Search demand from Google Search Console · Population from the "
    "INS 2014 census."
)
