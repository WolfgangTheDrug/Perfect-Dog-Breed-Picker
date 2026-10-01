import streamlit as st
import json

with open('app/public/panel.streamlit.json', 'r') as f:
    panel_config = json.load(f)

widgets = panel_config['widgets']
user_preferences = {
        "behavioral_&_care_traits": {},
        "physical_&_lifestyle_constraints": {},
        "special_requirements": {},
        "desired_temperament": {}
    }

st.header("🎯 Find Your Perfect Dog Breed")
st.markdown("Configure your preferences below. The engine uses these parameters to calculate precise fuzzy compatibility scores.")

# Initialize session state container if it doesn't exist
if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = user_preferences

with st.form("quiz_form"):

    st.subheader("1. Behavioral & Care Traits")
    st.caption("Adjust the double slider to your desired band. Toggle strict boundaries or dealbreakers as needed.")
    
    widget_type = widgets['bipolar_likert']
    
    section_inputs = {}
    for trait_name, elements in widget_type.items():
        cols = st.columns([3, 1, 1])
        temp = {}
        for i, (element_name, properties) in enumerate(elements.items()):
            with cols[i]:
                if element_name == 'slider': 
                    element_state = st.slider(**properties, key=f"{element_name}_{trait_name}")
                else:
                    element_state = st.checkbox(**properties, key=f"{element_name}_{trait_name}")
            temp[element_name] = element_state
        section_inputs[trait_name] = temp
    
    user_preferences['behavioral_&_care_traits'] = section_inputs
    st.divider()
    ###

    st.subheader("2. Physical & Lifestyle Constraints")

    widget_type = widgets['big_range']

    section_input = {}
    for trait_name, elements in widget_type.items():
        cols = st.columns([3, 1, 1])
        temp = {}
        for i, (element_name, properties) in enumerate(elements.items()):
            with cols[i]:
                if element_name == 'slider': 
                    element_state = st.slider(**properties, key=f"{element_name}_{trait_name}")
                else:
                    element_state = st.checkbox(**properties, key=f"{element_name}_{trait_name}")
            temp[element_name] = element_state
        section_input[trait_name] = temp

    user_preferences['physical_&_lifestyle_constraints'] = section_inputs
    st.divider()
    ###

    widget_type = widgets['segmented_control']

    requirements_map = {
        "Doesn't Matter": (False, True), 
        "Must Be": (True, True), 
        "Must NOT Be": (False, False)
    }
    st.subheader("3. Special Requirements")

    section_input = {}
    for trait_name, elements in widget_type.items():
        temp = {}
        for i, (element_name, properties) in enumerate(elements.items()):
            segmented_control_input = st.segmented_control(**properties) 

            temp[element_name] = {
                    "range": requirements_map[segmented_control_input],
                    "strict": True,
                    "dealbreaker": True
                }
        section_input[trait_name] = temp

    user_preferences['special_requirements'] = section_inputs
    st.divider()
    ###

    st.subheader("4. Desired Temperament Tags")

    widget_type = widgets['temperament']

    section_input = {}
    for trait_name, elements in widget_type.items():
        temp = {}
        for i, (element_name, properties) in enumerate(elements.items()):
            multiselect_input = st.multiselect(**properties) 

            temp[element_name] = {
                    "value": multiselect_input,
                    "strict": True,
                    "dealbreaker": True
                }
        section_input[trait_name] = temp

    user_preferences['desired_temperament'] = section_inputs
    ###
    submitted = st.form_submit_button("Save Preferences & Generate Matches", type="primary")

    if submitted:
        st.session_state.user_preferences = user_preferences
        st.success("Preferences saved successfully to session state!")

### dev only
st.sidebar.header("Live State Inspector")
st.sidebar.markdown("")
st.sidebar.json(st.session_state.user_preferences)