import streamlit as st
import pandas as pd
import os

# Configure page
st.set_page_config(page_title="Patent Validation Tool", layout="wide")

# Add debug info
st.write("Debug Info:")
st.write(f"Current directory: {os.getcwd()}")
st.write(f"Files in current directory: {os.listdir('.')}")

# Check if data directory exists
if os.path.exists('data'):
    st.write(f"Files in data directory: {os.listdir('data')}")
else:
    st.write("❌ Data directory does not exist!")

@st.cache_data
def load_data():
    """Load data with error handling for deployment"""
    try:
        # Try current directory first
        descriptions = pd.read_csv('data/pg_detail_desc_text_2001.tsv.zip', sep='\t', compression='zip')
        crosswalk = pd.read_csv('data/crosswalk.csv')
        st.success("✅ Real data files loaded successfully!")
        return descriptions, crosswalk
    except FileNotFoundError as e:
        st.error(f"❌ Data files not found: {e}")
        st.info("Using sample data instead...")
        
        # Create sample data
        descriptions = pd.DataFrame({
            'pgpub_id': ['US20010001', 'US20010002', 'US20010003'],
            'description_text': [
                'A novel method for improving semiconductor manufacturing processes.',
                'An innovative approach to wireless communication systems.',
                'A pharmaceutical composition for treating cardiovascular diseases.'
            ]
        })
        
        crosswalk = pd.DataFrame({
            'patent_id': ['US20010001', 'US20010002', 'US20010003'],
            'top1_industry_title': ['Semiconductor Manufacturing', 'Telecommunications', 'Pharmaceuticals'],
            'top1_similarity': [0.89, 0.92, 0.85],
            'top2_industry_title': ['Electronics', 'Wireless Technology', 'Biotechnology'],
            'top2_similarity': [0.76, 0.84, 0.79],
            'top3_industry_title': ['Materials Science', 'Signal Processing', 'Medical Devices'],
            'top3_similarity': [0.68, 0.77, 0.71]
        })
        
        return descriptions, crosswalk
    except Exception as e:
        st.error(f"❌ Unexpected error loading data: {e}")
        st.error(f"Error type: {type(e).__name__}")
        st.stop()

# Initialize session state for feedback storage
if 'feedback_data' not in st.session_state:
    st.session_state.feedback_data = []

# Load data
with st.spinner("Loading data..."):
    descriptions, crosswalk = load_data()

# Rest of your app code...
st.success("App is running successfully!")
st.write("If you can see this, the app startup is working.")