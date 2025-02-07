import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Streamlit UI Title
st.title("📊 PlanIt Survey - Graphical Representation")

# Path to the local CSV file
csv_file_path = 'planit_reviews.csv'  # Ensure this matches your actual CSV filename

# Read CSV File
df = pd.read_csv(csv_file_path)

# Check if required columns exist
required_columns = [
    "Overall Satisfaction", "Usefulness of Features", "Improvement Needed",
    "Effectiveness of Timetable", "Helpfulness of Mental Health Bot", "Likelihood to Recommend"
]

if all(col in df.columns for col in required_columns):

    # Graph 1: Distribution of Overall Satisfaction
    st.write("### Overall Satisfaction Distribution:")
    fig, ax = plt.subplots()
    sns.histplot(df["Overall Satisfaction"], bins=10, kde=True, palette="viridis", ax=ax)
    ax.set_xlabel("Satisfaction Score")
    ax.set_ylabel("Number of Responses")
    ax.set_title("Overall Satisfaction Levels")
    st.pyplot(fig)

    # Graph 2: Usefulness of Features
    st.write("### Usefulness of Features:")
    fig, ax = plt.subplots()
    sns.histplot(df["Usefulness of Features"], bins=10, kde=True, palette="coolwarm", ax=ax)
    ax.set_xlabel("Usefulness Score")
    ax.set_ylabel("Number of Responses")
    ax.set_title("Feature Usefulness Ratings")
    st.pyplot(fig)

    # Graph 3: Feature Preference Count
    st.write("### Most Preferred Feature:")
    fig, ax = plt.subplots()
    sns.countplot(y=df["Most Useful Feature"], palette="muted", ax=ax)
    ax.set_xlabel("Number of Users")
    ax.set_ylabel("Feature Name")
    ax.set_title("Most Useful Features (Survey)")
    st.pyplot(fig)

else:
    st.error("CSV file must contain the required survey columns.")

