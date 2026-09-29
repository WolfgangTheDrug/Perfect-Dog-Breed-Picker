import streamlit as st

st.header("🎯 Find Your Perfect Dog Breed")
st.markdown("Configure your preferences below. The engine uses these parameters to calculate precise fuzzy compatibility scores.")

# Initialize session state container if it doesn't exist
if "user_preferences" not in st.session_state:
    st.session_state.user_preferences = {
        "traits": {},
        "continuous": {},
        "binary": {},
        "tags": {}
    }

with st.form("quiz_form"):

    st.subheader("1. Behavioral & Care Traits (1 to 5 Scale)")
    st.caption("Adjust the double slider to your desired band. Toggle strict boundaries or dealbreakers as needed.")
    
    traits_to_show = {
        "energy": "Energy Level",
        "shedding": "Shedding Level",
        "barking": "Barking Tendency",
        "drooling": "Drooling Level",
        "trainability": "Trainability",
        "apartment_friendly": "Apartment Friendliness",
        "good_with_children": "Good with Children",
        "good_with_dogs": "Good with Other Dogs"
    }
    
    trait_inputs = {}
    for trait_key, trait_label in traits_to_show.items():
        col1, col2, col3 = st.columns([3,1,1])
        with col1:
            val_range = st.slider(trait_label, min_value=1, max_value=5, value=(1, 5), key=f"slider_{trait_key}")
        with col2:
            strict = st.checkbox("Strict Range", value=False, key=f"strict_{trait_key}", help="Disables soft-decay buffer")
        with col3:
            dealbreaker = st.checkbox("Dealbreaker", value=False, key=f"db_{trait_key}", help="Hard pre-pass filter")
            
        trait_inputs[trait_key] = {
            "range": val_range,
            "strict": strict,
            "dealbreaker": dealbreaker
        }
    
    st.divider()
    ###

    st.subheader("2. Physical & Lifestyle Constraints")
    
    col_1, col_2 = st.columns(2)
    with col_1:
        weight_range = st.slider("Target Weight Range (kg)", min_value=2, max_value=80, value=(10, 40), step=1)
    with col_2:
        exercise_range = st.slider("Daily Exercise Time (Minutes)", min_value=10, max_value=180, value=(30, 90), step=10)

    st.divider()
    ###
    
    st.subheader("3. Special Requirements")
    hypoallergenic_choice = st.radio(
        "Hypoallergenic Requirement",
        options=["Doesn't Matter", "Must Be Hypoallergenic", "Must NOT Be Hypoallergenic"],
        horizontal=True
    )

    st.divider()
    ###

    st.subheader("4. Desired Temperament Tags")
    sample_tags = ["Intelligent", "Playful", "Gentle", "Protective", "Independent", "Affectionate", "Energetic", "Calm", "Stubborn", "Curious"]
    selected_tags = st.multiselect("Select keywords you'd like your dog to embody:", options=sample_tags, default=["Intelligent", "Gentle"])

    ###
    submitted = st.form_submit_button("Save Preferences & Generate Matches", type="primary")

    if submitted:
        st.session_state.user_preferences = {
            "traits": trait_inputs,
            "continuous": {
                "weight_kg": weight_range,
                "exercise_minutes": exercise_range
            },
            "binary": {
                "hypoallergenic": hypoallergenic_choice
            },
            "tags": {
                "temperament": selected_tags
            }
        }
        st.success("Preferences saved successfully to session state!")

### dev only
st.sidebar.header("Live State Inspector")
st.sidebar.markdown("")
st.sidebar.json(st.session_state.user_preferences)