# Marine-Data-Analysis-Dashboard
A Streamlit dashboard for analyzing marine trawler data. Users can upload CSV files, select fish categories, and view the top 5 trawlers by catch and efficiency. The tool features interactive visualizations, distinct colors for fish types, and a search function to find trawler rankings by efficiency.
# Marine Data Analysis Dashboard

## Overview
The Marine Data Analysis Dashboard is a Streamlit-based web application designed to assist in the analysis of fishing data, focusing on the efficiency of marine trawlers and their fish catch performance. This project is part of a research initiative to explore the efficiency of different trawlers based on their fishing days and total catch, allowing users to make data-driven decisions.

## Features
- **CSV File Upload**: Upload your own CSV file containing fishing data.
- **Fish Category Selection**: Multi-selection tool for choosing specific fish categories, dynamically updating the analysis.
- **Top 5 Trawlers by Catch**: Display top 5 trawlers based on the selected fish categories, visualized with distinct colors for clarity.
- **Efficiency Analysis**: View the top trawlers by efficiency (total catch divided by fishing days) and a full chart of all trawlers.
- **Trawler Search**: Search for specific trawlers by name and retrieve their rank and efficiency details, with fuzzy matching for close results.

## Technologies Used
- **Python**: Main programming language.
- **Streamlit**: Web framework for building interactive dashboards.
- **Pandas**: Data manipulation and analysis.
- **Matplotlib & Seaborn**: Data visualization and graph plotting.
- **Difflib**: For fuzzy matching of trawler names.

## Requirements
To run this project locally, you need to have Python installed along with the following libraries:

- pandas
- streamlit
- seaborn
- matplotlib
- difflib (for fuzzy matching)

You can install the necessary dependencies by running the following command:

```bash
pip install -r requirements.txt
