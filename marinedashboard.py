import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Set Streamlit page config
st.set_page_config(page_title="Marine Dashboard", layout="wide")

# GitHub raw file URLs (Replace 'your-username' and 'your-repo' with actual values)
file_urls = {
    "Shrimp": "https://github.com/Tanjim96/Marine-Data-Analysis-Dashboard/blob/main/allfiles/shrimpdata.csv",
    "Fish Trawler": "https://github.com/Tanjim96/Marine-Data-Analysis-Dashboard/blob/main/allfiles/fishdata.csv",
    "Midwater": "https://github.com/Tanjim96/Marine-Data-Analysis-Dashboard/blob/main/allfiles/midwater.csv",
    "Trial": "https://github.com/Tanjim96/Marine-Data-Analysis-Dashboard/blob/main/allfiles/trial.csv",
}

# Dropdown to select dataset
selected_file = st.sidebar.selectbox("📂 Select a dataset", list(file_urls.keys()))

# Load the selected dataset
@st.cache_data
def load_data(url):
    return pd.read_csv(url)

df = load_data(file_urls[selected_file])

# Display dataset
st.subheader(f"📊 Dataset: {selected_file}")
st.write(df.head())

# Auto-adjusting chart
st.subheader("📈 Data Visualization")

# Sidebar option for user to select chart type
chart_type = st.sidebar.radio("Select Chart Type", ["Bar Chart", "Line Chart", "Scatter Plot"])

# Select columns for x and y axes
x_column = st.sidebar.selectbox("Select X-axis", df.columns)
y_column = st.sidebar.selectbox("Select Y-axis", df.columns)

# Plot dynamically based on user selection
fig, ax = plt.subplots(figsize=(10, 5))

if chart_type == "Bar Chart":
    sns.barplot(x=df[x_column], y=df[y_column], ax=ax)
elif chart_type == "Line Chart":
    sns.lineplot(x=df[x_column], y=df[y_column], ax=ax)
elif chart_type == "Scatter Plot":
    sns.scatterplot(x=df[x_column], y=df[y_column], ax=ax)

# Prevent overlapping labels
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")

# Display chart
st.pyplot(fig)

# Footer
st.write("📌 **Marine Data Dashboard** | Built with ❤️ using Streamlit")
