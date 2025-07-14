import streamlit as st
import pandas as pd
import os

# Configure page
st.set_page_config(page_title="Patent Validation Tool", layout="wide")

@st.cache_data
def load_data():
    try:
        # Load in chunks to reduce memory usage
        chunks = []
        for chunk in pd.read_csv('data/pg_detail_desc_text_2001.tsv.zip', 
                               sep='\t', compression='zip', chunksize=1000):
            chunks.append(chunk)
            if len(chunks) >= 10:  # Limit for deployment
                break
        
        descriptions = pd.concat(chunks, ignore_index=True)
        crosswalk = pd.read_csv('data/crosswalk.csv')
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()
    return descriptions, crosswalk

# Initialize session state for feedback storage
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = []

# Load data
with st.spinner("Loading data..."):
    descriptions, crosswalk = load_data()

# Merge data
data = pd.merge(descriptions, crosswalk, left_on='pgpub_id', right_on="patent_id", how="inner")
data = data.drop(['pgpub_id', 'description_length'], axis=1)

# Check if data is loaded successfully
if data.empty:
    st.error("No data available after merging. Please check your data files.")
    st.stop()

# --- Setup UI ---
st.sidebar.title("Patent Lookup")

# Add data info in sidebar
st.sidebar.info(f"Total patents: {len(data['patent_id'].unique())}")

patent_id = st.sidebar.selectbox("Choose a Patent ID:", data["patent_id"].unique())

# --- Get selected row ---
try:
    row = data[data["patent_id"] == patent_id].iloc[0]
except IndexError:
    st.error(f"Patent ID {patent_id} not found in data.")
    st.stop()

# --- Display ---
st.title(f"Patent ID: {row['patent_id']}")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Description")
    st.write(row["description_text"])

with col2:
    st.subheader("Patent Info")
    st.write(f"**Patent ID:** {row['patent_id']}")

st.subheader("Top Matched Industries")

feedback = {}
cols = st.columns(3)

for i in range(1, 4):
    with cols[i-1]:
        industry = row[f"top{i}_industry_title"]
        similarity = row[f"top{i}_similarity"]
        
        st.markdown(f"**{i}. {industry}**")
        st.markdown(f"Similarity: {similarity:.2f}")
        
        feedback[f"industry_{i}_feedback"] = st.radio(
            f"Is match {i} relevant?",
            ["Yes", "No", "Uncertain"],
            key=f"feedback_{i}",
            horizontal=True
        )

# --- Submit feedback ---
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Save Feedback", type="primary"):
        result = {
            "patent_id": row["patent_id"],
            "industry_1": row["top1_industry_title"],
            "industry_2": row["top2_industry_title"], 
            "industry_3": row["top3_industry_title"],
            "similarity_1": row["top1_similarity"],
            "similarity_2": row["top2_similarity"],
            "similarity_3": row["top3_similarity"],
            "industry_1_feedback": feedback["industry_1_feedback"],
            "industry_2_feedback": feedback["industry_2_feedback"],
            "industry_3_feedback": feedback["industry_3_feedback"]
        }
        
        # Check if feedback already exists for this patent
        existing_feedback = [f for f in st.session_state.feedback_data if f['patent_id'] == patent_id]
        if existing_feedback:
            # Update existing feedback
            for i, f in enumerate(st.session_state.feedback_data):
                if f['patent_id'] == patent_id:
                    st.session_state.feedback_data[i] = result
                    break
            st.success("Feedback updated!")
        else:
            # Add new feedback
            st.session_state.feedback_data.append(result)
            st.success("Feedback saved!")

with col2:
    if st.button("Clear Current Feedback"):
        # Remove feedback for current patent
        st.session_state.feedback_data = [f for f in st.session_state.feedback_data if f['patent_id'] != patent_id]
        st.success("Current feedback cleared!")
        st.rerun()

# --- Display collected feedback ---
if st.session_state.feedback_data:
    st.subheader("Collected Feedback")
    
    feedback_df = pd.DataFrame(st.session_state.feedback_data)
    
    # Show feedback for current patent
    selected_feedback = feedback_df[feedback_df['patent_id'] == patent_id]
    if not selected_feedback.empty:
        st.success(f"Feedback exists for Patent ID: {patent_id}")
        with st.expander("View Current Patent Feedback"):
            st.dataframe(selected_feedback, use_container_width=True)
    else:
        st.info("No feedback collected for this patent yet.")
    
    # Show summary statistics
    st.subheader("Feedback Summary")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Patents Reviewed", len(feedback_df))
    
    with col2:
        yes_count = sum([
            (feedback_df['industry_1_feedback'] == 'Yes').sum(),
            (feedback_df['industry_2_feedback'] == 'Yes').sum(),
            (feedback_df['industry_3_feedback'] == 'Yes').sum()
        ])
        st.metric("Total 'Yes' Matches", yes_count)
    
    with col3:
        no_count = sum([
            (feedback_df['industry_1_feedback'] == 'No').sum(),
            (feedback_df['industry_2_feedback'] == 'No').sum(),
            (feedback_df['industry_3_feedback'] == 'No').sum()
        ])
        st.metric("Total 'No' Matches", no_count)
    
    # Download feedback as CSV
    csv = feedback_df.to_csv(index=False)
    st.download_button(
        label="Download All Feedback (.csv)",
        data=csv,
        file_name="validation_feedback.csv",
        mime="text/csv",
        type="secondary"
    )
    
    # Option to clear all feedback
    # if st.button("⚠️ Clear All Feedback", help="This will delete all collected feedback"):
    #     st.session_state.feedback_data = []
    #     st.success("All feedback cleared!")
    #     st.rerun()

else:
    st.info("No feedback collected yet. Start reviewing patents!")

# --- Footer ---
st.markdown("---")
st.markdown("Patent Validation Tool - Review industry matches and provide feedback")
