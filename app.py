import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import difflib

# Configure the page
st.set_page_config(
    page_title="Marine Data Analysis Dashboard",
    page_icon="🚢",
    layout="wide"
)


# Cache data loading
@st.cache_data
def load_dataset(filename):
    df = pd.read_csv(Path("data") / filename)

    # Handle different column names for Total
    if 'Total (Kg)' in df.columns:
        df = df.rename(columns={'Total (Kg)': 'Total'})

    # Remove 'Sl. No' if it exists
    if 'Sl. No' in df.columns:
        df = df.drop('Sl. No', axis=1)

    return df


@st.cache_data
def calculate_efficiency(df):
    df = df.copy()
    df['Efficiency'] = df['Total'] / df['Fishing Days']
    df['Rank'] = df['Efficiency'].rank(ascending=False, method="min").astype(int)
    return df


def get_fish_columns(df, dataset_type):
    """Get relevant fish columns based on dataset type"""
    exclude_cols = ['Sl. No', 'Trawler Name', 'Fishing Days', 'Total', 'Efficiency', 'Rank']

    if dataset_type == 'shrimp':
        # For shrimp dataset, group columns by type
        shrimp_cols = [col for col in df.columns if 'Shrimp' in col and col != 'Total Shrimp']
        fish_cols = [col for col in df.columns if col not in exclude_cols + shrimp_cols + ['Total Shrimp']]
        return {
            'Shrimp Species': shrimp_cols,
            'Other Fish': fish_cols
        }
    else:
        # For regular datasets
        return {
            'Fish Species': [col for col in df.columns if col not in exclude_cols]
        }


def create_top_trawlers_chart(df, selected_fish):
    """Create a stacked bar chart for top 5 trawlers with distinct colors for each fish"""
    # Calculate total for ranking
    df["Total_Selected"] = df[selected_fish].sum(axis=1)
    top5_trawlers = df.nlargest(5, "Total_Selected")

    fig, ax = plt.subplots(figsize=(12, 6))

    # Create stacked bars with different colors for each fish type
    bottom = np.zeros(len(top5_trawlers))
    # Use different color palettes for shrimp and fish
    if any('Shrimp' in fish for fish in selected_fish):
        palette = sns.color_palette("Reds_r", n_colors=len(selected_fish))
    else:
        palette = sns.color_palette("husl", n_colors=len(selected_fish))

    for idx, fish in enumerate(selected_fish):
        values = top5_trawlers[fish].values
        ax.barh(top5_trawlers['Trawler Name'], values, left=bottom,
                label=fish, color=palette[idx])
        bottom += values

    # Add value labels on bars
    for i, total in enumerate(top5_trawlers["Total_Selected"]):
        ax.text(total, i, f' {total:,.0f}', va='center')

    ax.set_title("Top 5 Trawlers by Selected Species Catch")
    ax.set_xlabel("Total Catch (Kg)")
    plt.legend(title="Species", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    return fig


def create_efficiency_chart(df, num_trawlers=5):
    """Create an efficiency bar chart for top N trawlers"""
    top_trawlers_efficiency = df.nlargest(num_trawlers, 'Efficiency')[['Trawler Name', 'Efficiency']]

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(
        data=top_trawlers_efficiency,
        x='Trawler Name',
        y='Efficiency',
        palette="plasma",
        ax=ax
    )

    # Add value labels
    for i, v in enumerate(top_trawlers_efficiency["Efficiency"]):
        ax.text(i, v, f'{v:.2f}', ha='center', va='bottom')

    plt.xticks(rotation=45, ha='right')
    ax.set_title(f"Top {num_trawlers} Trawlers by Efficiency")
    ax.set_ylabel("Efficiency (Catch/Day)")
    plt.tight_layout()
    return fig


def create_all_trawlers_efficiency_chart(df):
    """Create a bar chart for all trawlers' efficiency"""
    sorted_df = df.sort_values(by='Efficiency', ascending=False)

    fig, ax = plt.subplots(figsize=(16, 8))
    sns.barplot(
        data=sorted_df,
        x='Trawler Name',
        y='Efficiency',
        palette="plasma",
        ax=ax
    )

    plt.xticks(rotation=90)
    ax.set_title('All Trawlers by Fish Catching Efficiency')
    ax.set_ylabel("Efficiency (Catch/Day)")
    plt.tight_layout()
    return fig


def main():
    st.title("Marine Data Analysis Dashboard 🚢🐟")

    # Sidebar
    st.sidebar.header("Data Selection")

    # File selection dropdown
    available_files = ["shrimp.csv", "fish_trawler.csv", "midwater.csv", "trial.csv"]
    selected_file = st.sidebar.selectbox("Select Dataset:", available_files)

    try:
        # Load and process data
        df = load_dataset(selected_file)
        df = calculate_efficiency(df)

        # Determine dataset type and get appropriate columns
        dataset_type = 'shrimp' if selected_file == 'shrimp.csv' else 'regular'
        species_groups = get_fish_columns(df, dataset_type)

        # Create species selection for each group
        selected_fish = []
        for group_name, species_list in species_groups.items():
            st.sidebar.subheader(group_name)
            selected = st.sidebar.multiselect(
                f"Select {group_name}:",
                species_list,
                default=[species_list[0]] if species_list else None
            )
            selected_fish.extend(selected)

        if not selected_fish:
            st.warning("Please select at least one species to analyze.")
            return

        # Layout using columns
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Top 5 Trawlers by Catch")
            fig_top5 = create_top_trawlers_chart(df, selected_fish)
            st.pyplot(fig_top5)

            st.subheader("Trawler Search")
            search_trawler = st.text_input("Enter Trawler Name:")
            if search_trawler:
                matches = difflib.get_close_matches(
                    search_trawler,
                    df['Trawler Name'],
                    n=1,
                    cutoff=0.6
                )
                if matches:
                    trawler = matches[0]
                    trawler_data = df[df['Trawler Name'] == trawler].iloc[0]

                    st.success(f"Found: {trawler}")
                    metrics_col1, metrics_col2 = st.columns(2)
                    with metrics_col1:
                        st.metric("Rank", f"#{trawler_data['Rank']}")
                    with metrics_col2:
                        st.metric("Efficiency", f"{trawler_data['Efficiency']:.2f}")
                else:
                    st.error("No matching trawler found.")

        with col2:
            st.subheader("Top Trawlers Efficiency")
            fig_eff = create_efficiency_chart(df)
            st.pyplot(fig_eff)

            st.subheader("All Trawlers Efficiency")
            fig_all = create_all_trawlers_efficiency_chart(df)
            st.pyplot(fig_all)

        # Display raw data with toggle
        if st.sidebar.checkbox("Show Raw Data"):
            st.subheader("Raw Data")
            st.dataframe(df)

    except FileNotFoundError:
        st.error("Please ensure the data files are in the 'data' directory.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
