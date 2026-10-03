import streamlit as st

st.set_page_config(
    page_title="BreedMatch Pro",
    page_icon="🐕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define the multi-page structure
pages = [
    st.Page(page="pages/0_home.py", title="Home", icon="🏠", default=True),
    st.Page(page="pages/1_panel.py", title="Find Your Perfect Dog Breed", icon="🎯"),
]

# Run navigation router
navigation = st.navigation(pages)
navigation.run()