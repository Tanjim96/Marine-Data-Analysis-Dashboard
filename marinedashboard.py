import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import difflib

st.title("Marine Data Analysis Dashboard 🚢🐟")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    df['Efficiency'] = df['Total'] / df['Fishing Days']
    df['Rank'] = df['Efficiency'].rank(ascending=False, method="min").astype(int)
    sorted_efficiency_df = df.sort_values(by="Efficiency", ascending=False)

    fish_columns = df.columns[3:-1]

    selected_fish = st.multiselect("Select Fish Type(s):", fish_columns, default=[fish_columns[0]])

    if selected_fish:
        df["Selected Fish Total"] = df[selected_fish].sum(axis=1)

        top5_trawlers = df[['Trawler Name', "Selected Fish Total"]].sort_values(by="Selected Fish Total", ascending=False).head(5)

        palette = sns.color_palette("husl", len(selected_fish))

        graph_height = 5 + (len(selected_fish) * 0.5)

        st.subheader(f"Top 5 Trawlers for {', '.join(selected_fish)}")
        fig, ax = plt.subplots(figsize=(12, graph_height))

        for i, fish in enumerate(selected_fish):
            fish_data = df[['Trawler Name', fish]].sort_values(by=fish, ascending=False).head(5)
            sns.barplot(data=fish_data, x=fish, y="Trawler Name", color=palette[i], label=fish, ax=ax)

        ax.set_xlabel("Total Catch")
        ax.set_ylabel("Trawler Name")
        ax.set_title("Top 5 Trawlers by Selected Fish")
        ax.legend(title="Fish Type")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    st.subheader("Trawler Efficiency Analysis")

    top_trawlers_efficiency_df = df[['Trawler Name', 'Efficiency']].sort_values(by='Efficiency', ascending=False).head(5)

    fig, ax = plt.subplots(figsize=(12, 7))
    sns.barplot(data=top_trawlers_efficiency_df, x="Efficiency", y="Trawler Name", palette="magma", ax=ax)
    ax.set_xlabel("Efficiency (Total Catch / Fishing Days)")
    ax.set_ylabel("Trawler Name")
    ax.set_title("Top Trawlers by Efficiency")
    plt.xticks(rotation=45)
    st.pyplot(fig)

    fig, ax = plt.subplots(figsize=(14, 10))
    sorted_trawlers_efficiency_df = df.sort_values(by='Efficiency', ascending=False)
    sns.barplot(data=sorted_trawlers_efficiency_df, x="Efficiency", y="Trawler Name", palette="viridis", ax=ax)
    ax.set_xlabel("Efficiency (Total Catch / Fishing Days)")
    ax.set_ylabel("Trawler Name")
    ax.set_title("All Trawlers by Efficiency")
    plt.xticks(rotation=45)
    st.pyplot(fig)

st.subheader("🔍 Search Trawler Efficiency Rank")
search_trawler = st.text_input("Enter Trawler Name:")

if search_trawler:
    matches = difflib.get_close_matches(search_trawler, sorted_trawlers_efficiency_df['Trawler Name'], n=1, cutoff=0.7)

    if matches:
        best_match = matches[0]
        trawler_data = sorted_trawlers_efficiency_df[sorted_trawlers_efficiency_df['Trawler Name'] == best_match]
        trawler_rank = trawler_data['Rank'].values[0]
        trawler_efficiency = trawler_data['Efficiency'].values[0]

        st.success(f"✅ Found: **{best_match}** (Confidence: 70%)")
        st.write(f"🏅 Rank: **{trawler_rank}**")
        st.write(f"⚙️ Efficiency: **{trawler_efficiency:.2f}**")
    else:
        st.error("❌ No close match found. Please check the name.")
