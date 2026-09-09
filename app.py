"""
Marine Data Analysis Dashboard
--------------------------------
Interactive Streamlit dashboard for exploring trawler fishing catch data:
catch volumes by species, fleet efficiency, and per-trawler lookup.

Run with:  streamlit run marine_dashboard.py
Expects CSV files inside a ./data folder (e.g. shrimp.csv, fish_trawler.csv).
"""

import difflib
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# --------------------------------------------------------------------------
# Page configuration & light theming
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Marine Data Analysis Dashboard",
    page_icon="🚢",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY_COLOR = "#0E7C7B"

st.markdown(
    """
    <style>
    /* Use Streamlit's own theme variables instead of fixed colors, so this
       adapts correctly whether the user has a light or dark theme active. */
    div[data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.25);
        border-radius: 10px;
        padding: 12px 16px;
    }
    section[data-testid="stSidebar"] {
        background-color: var(--secondary-background-color);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_DIR = Path("data")
EXCLUDED_COLS = {"Sl. No", "Trawler Name", "Fishing Days", "Total", "Efficiency", "Rank"}
FALLBACK_FILES = ["shrimp.csv", "fish_trawler.csv", "midwater.csv", "trial.csv"]


# --------------------------------------------------------------------------
# Data loading & processing
# --------------------------------------------------------------------------
@st.cache_data
def discover_datasets(data_dir: Path) -> list[str]:
    """Find every CSV file actually present in the data directory."""
    if not data_dir.exists():
        return []
    return sorted(f.name for f in data_dir.glob("*.csv"))


@st.cache_data
def load_dataset(filename: str) -> pd.DataFrame:
    """Load and lightly clean a trawler catch CSV file."""
    df = pd.read_csv(DATA_DIR / filename)

    if "Total (Kg)" in df.columns:
        df = df.rename(columns={"Total (Kg)": "Total"})
    if "Sl. No" in df.columns:
        df = df.drop(columns="Sl. No")

    required = {"Trawler Name", "Fishing Days", "Total"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Dataset is missing required column(s): {', '.join(sorted(missing))}")

    # Coerce every numeric column, turning stray blanks/text into 0 instead of crashing
    numeric_cols = [c for c in df.columns if c != "Trawler Name"]
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce").fillna(0)

    return df


@st.cache_data
def calculate_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    """Add per-day catch efficiency and a fleet-wide rank (safe against 0 fishing days)."""
    df = df.copy()
    safe_days = df["Fishing Days"].replace(0, np.nan)
    df["Efficiency"] = (df["Total"] / safe_days).fillna(0)
    df["Rank"] = df["Efficiency"].rank(ascending=False, method="min").astype(int)
    return df


def get_species_groups(df: pd.DataFrame, dataset_type: str) -> dict[str, list[str]]:
    """Group selectable species columns; shrimp datasets get split into two groups."""
    if dataset_type == "shrimp":
        shrimp_cols = [c for c in df.columns if "Shrimp" in c and c != "Total Shrimp"]
        other_cols = [
            c for c in df.columns
            if c not in EXCLUDED_COLS and c not in shrimp_cols and c != "Total Shrimp"
        ]
        groups: dict[str, list[str]] = {}
        if shrimp_cols:
            groups["Shrimp Species"] = shrimp_cols
        if other_cols:
            groups["Other Fish"] = other_cols
        return groups

    return {"Fish Species": [c for c in df.columns if c not in EXCLUDED_COLS]}


# --------------------------------------------------------------------------
# Chart builders — Plotly, so every bar/slice is hoverable and zoomable
# --------------------------------------------------------------------------
def chart_top_trawlers(df: pd.DataFrame, species: list[str], top_n: int) -> go.Figure:
    """Stacked horizontal bar chart of the top N trawlers by selected species."""
    work = df[["Trawler Name"] + species].copy()
    work["Total Selected"] = work[species].sum(axis=1)
    top = work.nlargest(top_n, "Total Selected").sort_values("Total Selected")

    fig = go.Figure()
    for sp in species:
        fig.add_trace(go.Bar(
            y=top["Trawler Name"], x=top[sp], name=sp, orientation="h",
            hovertemplate=f"<b>%{{y}}</b><br>{sp}: %{{x:,.0f}} kg<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        title=f"Top {top_n} Trawlers by Selected Species Catch",
        xaxis_title="Total Catch (Kg)", yaxis_title="",
        legend_title="Species", height=420,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def chart_efficiency(df: pd.DataFrame, top_n: int) -> go.Figure:
    """Bar chart of the top N most efficient trawlers (catch per fishing day)."""
    top = df.nlargest(top_n, "Efficiency").sort_values("Efficiency")
    fig = px.bar(
        top, x="Efficiency", y="Trawler Name", orientation="h",
        color="Efficiency", color_continuous_scale="Teal",
        text=top["Efficiency"].round(2),
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        title=f"Top {top_n} Trawlers by Efficiency (Catch/Day)",
        height=420, coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def chart_all_efficiency(df: pd.DataFrame) -> go.Figure:
    """Fleet-wide efficiency ranking across every trawler in the dataset."""
    sorted_df = df.sort_values("Efficiency", ascending=False)
    fig = px.bar(
        sorted_df, x="Trawler Name", y="Efficiency",
        color="Efficiency", color_continuous_scale="Teal",
    )
    fig.update_layout(
        title="Fleet-wide Efficiency Ranking",
        xaxis_tickangle=-90, height=450,
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


def chart_species_share(df: pd.DataFrame, species: list[str]) -> go.Figure:
    """Donut chart showing each selected species' share of total fleet catch."""
    totals = df[species].sum().sort_values(ascending=False)
    fig = px.pie(
        values=totals.values, names=totals.index, hole=0.45,
        color_discrete_sequence=px.colors.sequential.Teal_r,
    )
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(title="Fleet-wide Species Share", height=420, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def chart_efficiency_distribution(df: pd.DataFrame) -> go.Figure:
    """Histogram showing how efficiency is distributed across the fleet."""
    fig = px.histogram(df, x="Efficiency", nbins=20, color_discrete_sequence=[PRIMARY_COLOR])
    fig.update_layout(
        title="Distribution of Trawler Efficiency",
        xaxis_title="Efficiency (Catch/Day)", yaxis_title="Number of Trawlers",
        height=350, margin=dict(l=10, r=10, t=50, b=10),
    )
    return fig


# --------------------------------------------------------------------------
# UI sections
# --------------------------------------------------------------------------
def render_kpis(df: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Trawlers", f"{len(df):,}")
    c2.metric("Total Catch", f"{df['Total'].sum():,.0f} kg")
    c3.metric("Avg Efficiency", f"{df['Efficiency'].mean():.2f} kg/day")
    top_trawler = df.loc[df["Efficiency"].idxmax(), "Trawler Name"] if len(df) else "—"
    c4.metric("Top Performer", top_trawler)


def render_search(df: pd.DataFrame) -> None:
    st.subheader("🔍 Trawler Lookup")
    names = df["Trawler Name"].tolist()
    choice = st.selectbox("Pick a trawler:", options=["—"] + names, index=0)

    query = None
    if choice != "—":
        query = choice
    else:
        typed = st.text_input("...or search by partial / misspelled name:")
        if typed:
            matches = difflib.get_close_matches(typed, names, n=3, cutoff=0.5)
            if matches:
                query = st.radio("Closest matches:", matches, horizontal=True)
            else:
                st.error("No matching trawler found.")

    if query:
        row = df[df["Trawler Name"] == query].iloc[0]
        m1, m2, m3 = st.columns(3)
        m1.metric("Rank", f"#{int(row['Rank'])} of {len(df)}")
        m2.metric("Efficiency", f"{row['Efficiency']:.2f} kg/day")
        m3.metric("Total Catch", f"{row['Total']:,.0f} kg")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    st.title("🚢🐟 Marine Data Analysis Dashboard")
    st.caption("Explore trawler catch volumes, species composition, and fishing efficiency across the fleet.")

    st.sidebar.header("📂 Data Selection")
    available_files = discover_datasets(DATA_DIR) or FALLBACK_FILES
    selected_file = st.sidebar.selectbox("Dataset:", available_files)

    try:
        df = load_dataset(selected_file)
    except FileNotFoundError:
        st.error(f"Couldn't find `{selected_file}` inside the `data/` folder. Add the CSV and reload.")
        return
    except ValueError as e:
        st.error(str(e))
        return
    except Exception as e:
        st.error(f"Couldn't read `{selected_file}`: {e}")
        return

    if df.empty:
        st.warning("This dataset is empty.")
        return

    df = calculate_efficiency(df)
    dataset_type = "shrimp" if "shrimp" in selected_file.lower() else "regular"
    species_groups = get_species_groups(df, dataset_type)

    st.sidebar.header("🐟 Species Filter")
    selected_species: list[str] = []
    for group_name, species_list in species_groups.items():
        with st.sidebar.expander(group_name, expanded=True):
            default = species_list[:3]
            picked = st.multiselect(f"Select {group_name.lower()}:", species_list, default=default, key=group_name)
            selected_species.extend(picked)

    st.sidebar.header("⚙️ Display Options")
    n_trawlers = len(df)
    if n_trawlers <= 1:
        # Slider needs min_value != max_value, so skip it for tiny datasets
        top_n = n_trawlers
        st.sidebar.caption(f"Only {n_trawlers} trawler in this dataset — showing it directly.")
    else:
        max_n = min(20, n_trawlers)
        top_n = st.sidebar.slider(
            "Number of trawlers to highlight:", min_value=1, max_value=max_n, value=min(5, max_n)
        )

    render_kpis(df)
    st.divider()

    tab_overview, tab_efficiency, tab_species, tab_search, tab_data = st.tabs(
        ["📊 Overview", "⚡ Efficiency", "🐠 Species Mix", "🔍 Trawler Lookup", "📄 Raw Data"]
    )

    with tab_overview:
        if selected_species:
            st.plotly_chart(chart_top_trawlers(df, selected_species, top_n), width='stretch')
        else:
            st.info("Pick species in the sidebar to see the top-catch chart.")

    with tab_efficiency:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(chart_efficiency(df, top_n), width='stretch')
        with col2:
            st.plotly_chart(chart_efficiency_distribution(df), width='stretch')
        st.plotly_chart(chart_all_efficiency(df), width='stretch')

    with tab_species:
        if selected_species:
            st.plotly_chart(chart_species_share(df, selected_species), width='stretch')
        else:
            st.info("Pick species in the sidebar to see the fleet-wide species mix.")

    with tab_search:
        render_search(df)

    with tab_data:
        st.dataframe(df, width='stretch')
        st.download_button(
            "⬇️ Download this dataset as CSV",
            df.to_csv(index=False).encode("utf-8"),
            file_name=f"processed_{selected_file}",
            mime="text/csv",
        )


if __name__ == "__main__":
    main()
