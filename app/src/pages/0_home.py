import streamlit as st

st.title("Dogs are your friends")
st.subheader("Choose them wisely")

st.markdown("""
[text]
""")

st.divider()

st.markdown("### Ready to find your companion?")
if st.button("🚀 Start the Preference Quiz", type="primary", use_container_width=True):
    st.switch_page("pages/1_panel.py")
