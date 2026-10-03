from typing import Any, Dict, List

import streamlit as st
import json

from backend.engine.engine import BreedMatchEngine
from backend.api.api import fetch_dog_breeds, get_breed_image_lazily

def switch_render():
    st.session_state.submitted = not st.session_state.submitted

if 'submitted' not in st.session_state:
    st.session_state.submitted = False

if not st.session_state.submitted:
    with open('app/public/panel.streamlit.json', 'r') as f:
        panel_config = json.load(f)

    user_preferences = {
            'behavioral_&_care_traits': {},
            'physical_&_lifestyle_constraints': {},
            'special_requirements': {},
            'desired_temperament': {}
        }
    # Initialize session state container if it doesn't exist
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = user_preferences

    st.header('🎯 Find Your Perfect Dog Breed')
    st.markdown('Configure your preferences below. The engine uses these parameters to calculate precise fuzzy compatibility scores.')

    with st.form('form'):
        for section_name in user_preferences.keys():
            section = panel_config[section_name]

            for text in section['texts']:
                getattr(st, text)(section['texts'][text])
            
            section_inputs = {}
            for trait_name, elements in section['widgets'].items():
                additional_cols_count = len(elements.items()) - 1
                cols = st.columns([3] + [1] * additional_cols_count)
                temp = {}
                for i in range(len(cols)):
                    if additional_cols_count - i >= 0:
                        element_name, properties = list(elements.items())[i]
                        widget_name, input_key = str.rsplit(element_name, '_', 1)
                        with cols[i]:
                            element_state = getattr(st, widget_name)(**properties, key=f'{input_key}_{trait_name}')
                        temp[input_key] = element_state
                    else:
                        temp['strict'] = section_name != 'desired_temperament'
                        temp['dealbreaker"'] = section_name != 'desired_temperament'
                section_inputs[trait_name] = temp
            
            user_preferences[section_name] = section_inputs
            st.divider()
            ###

            # section_name = 'physical_&_lifestyle_constraints'
            # section = panel_config[section_name]
            # getattr(st, 'subheader')(f'{i}. {section['texts']['subheader']}')
            # if 'caption' in section['texts']:
            #     getattr(st, 'caption')(section['texts']['caption'])

            # widgets = section['widgets']

            # section_input = {}
            # for trait_name, elements in widgets.items():
            #     cols = st.columns([3, 1, 1])
            #     temp = {}
            #     for i, (element_name, properties) in enumerate(elements.items()):
            #         widget_name, input_key = str.split(element_name, '_', 1)
            #         getattr(st, widget_name)
            #         with cols[i]:
            #             if widget_name == 'slider': 
            #                 element_state = getattr(st, widget_name)(**properties, key=f'{element_name}_{trait_name}')
            #             else:
            #                 element_state = getattr(st, widget_name)(**properties, key=f'{element_name}_{trait_name}')
            #         temp[element_name] = element_state
            #     section_input[trait_name] = temp

            # user_preferences['physical_&_lifestyle_constraints'] = section_inputs
            # st.divider()
            # ###

            # section_name = 'special_requirements'
            # section = panel_config[section_name]
            # getattr(st, 'subheader')(f'{i}. {section['texts']['subheader']}')
            # if 'caption' in section['texts']:
            #     getattr(st, 'caption')(section['texts']['caption'])
            
            # widgets = section['widgets']

            # requirements_map = {
            #     'Doesn\'t Matter': (False, True), 
            #     'Must Be': (True, True), 
            #     'Must NOT Be': (False, False)
            # }

            # section_input = {}
            # for trait_name, elements in widgets.items():
            #     temp = {}
            #     for i, (element_name, properties) in enumerate(elements.items()):
            #         segmented_control_input = st.segmented_control(**properties) 

            #         temp[element_name] = {
            #                 'range': requirements_map[segmented_control_input],
            #                 'strict': True,
            #                 'dealbreaker': True
            #             }
            #     section_input[trait_name] = temp

            # user_preferences['special_requirements'] = section_inputs
            # st.divider()
            # ###

            # section_name = 'desired_temperament'
            # section = panel_config[section_name]
            # getattr(st, 'subheader')(f'{i}. {section['texts']['subheader']}')
            # if 'caption' in section['texts']:
            #     getattr(st, 'caption')(section['texts']['caption'])

            # # st.subheader('4. Desired Temperament Tags')

            # widget = section['widgets']

            # section_input = {}
            # for trait_name, elements in widget.items():
            #     temp = {}
            #     for i, (element_name, properties) in enumerate(elements.items()):
            #         multiselect_input = st.multiselect(**properties) 

            #         temp[element_name] = {
            #                 'value': multiselect_input,
            #                 'strict': True,
            #                 'dealbreaker': True
            #             }
            #     section_input[trait_name] = temp

            # user_preferences['desired_temperament'] = section_inputs
        
        
        ###
        # TODO: DEL
        st.session_state.user_preferences = user_preferences
        
        # TODO: KEEP
        submitted = st.form_submit_button(
            'Save Preferences & Generate Matches', 
            type='primary', 
            on_click=switch_render)
        if submitted:
            st.session_state.user_preferences = user_preferences
            st.success('Preferences saved successfully to session state!')
            
            
else:
    st.header("Results")
    st.markdown("Here are the top-ranking breeds tailored precisely to your preferences.")

# 1. Verify that preferences exist in session state
    user_preferences_dictionary: Dict[str, Any] = st.session_state.get("user_preferences", {})
    is_quiz_completed: bool = bool(user_preferences_dictionary)

    if not is_quiz_completed:
        st.warning("⚠️ You haven't completed the preference quiz yet!")
        st.button("Go to Quiz", type="primary", on_click=switch_render)
            
    else:
        # 2. Fetch raw API data
        with st.spinner("Fetching breed database and running matching algorithms..."):
            raw_breeds_data: List[Dict[str, Any]] = fetch_dog_breeds()

        engine = BreedMatchEngine(user_preferences_dictionary, raw_breeds_data)
        for result in engine.match(top_n=100).to_list():
            st.write(result)    
            
        # # 3. Instantiate the OOP Backend Engine and execute
        # matcher_engine = BreedMatcherEngine(
        #     user_preferences=user_preferences_dictionary, 
        #     breeds_data=raw_breeds_data
        # )
        # ranked_matching_breeds: List[Dict[str, Any]] = matcher_engine.run()

        # # 4. Render the output
        # has_no_matches: bool = (len(ranked_matching_breeds) == 0)
        # if has_no_matches:
        #     st.error("No breeds matched your exact combination of strict constraints and dealbreakers. Try loosening your sliders!")
        #     if st.button("Modify Preferences"):
        #         st.switch_page("views/quiz.py")
        # else:
        #     st.success(f"Successfully found {len(ranked_matching_breeds)} compatible breeds!")
            
        #     # Display top matches in a clean layout
        #     for breed_record in ranked_matching_breeds:  # Top 10 spotlight
        #         breed_name: str = breed_record.get("name", "Unknown")
        #         match_score: float = breed_record.get("match_score", 0.0)
        #         breed_description: str = breed_record.get("description", "")
        #         breed_id_string: str = breed_record.get("id", "")
        #         lazy_image_url: str = get_breed_image_lazily(breed_id_string)
                
        #         with st.container(border=True):
        #             col_photo, col_title, col_score = st.columns([2, 4, 1])
        #             with col_photo:
        #                 if lazy_image_url:
        #                     st.image(lazy_image_url, width='stretch', caption=breed_record.get("name"))
        #             with col_title:
        #                 st.subheader(breed_name)
        #             with col_score:
        #                 st.metric(label="Match", value=f"{match_score}%")
                    
                    
        #             st.write(breed_description)

### dev only
st.sidebar.header('Live State Inspector')
st.sidebar.json(st.session_state.user_preferences)