import streamlit as st
import json

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
    submitted = st.form_submit_button('Save Preferences & Generate Matches', type='primary')
    if submitted:
        st.session_state.user_preferences = user_preferences
        st.success('Preferences saved successfully to session state!')

### dev only
st.sidebar.header('Live State Inspector')
st.sidebar.markdown('')
st.sidebar.json(st.session_state.user_preferences)