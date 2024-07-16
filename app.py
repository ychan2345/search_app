import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title='NPPES NPI Registry Application', layout='wide', page_icon=":page_facing_up:")

st.header('NPPES NPI Registry Application :page_facing_up:')

menu = ['Introduction', 'Report']
choice = st.sidebar.selectbox("Main Menu", menu)

if choice == 'Introduction':
    st.markdown('''
                    <div align='center'><h1 style="color:blue"><font size="5"> Welcome to NPPES NPI Registry Application </font> </h1></div> <br>                    
                    The application is designed to facilitate easy retrieval of data from the NPPES NPI Registry's website (https://npiregistry.cms.hhs.gov/search).
                    Users can extract Ophthalmology and Optometrist information by entering the city and state.
                 ''', unsafe_allow_html=True)

elif choice == 'Report':
    Taxonomy_choice = st.sidebar.selectbox("Taxonomy", ['Ophthalmology', 'Optometrist', 'Both'])
    city = st.sidebar.text_input("Please enter a city")
    state = st.sidebar.selectbox("Please select a state", [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
        'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA',
        'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
    ])

    if st.sidebar.button('Generate Report'):
        if city == '' or state == '':
            st.write("Please enter both city and state")
        else:
            def fetch_providers_by_taxonomy(city, state, taxonomy_description):
                base_url = "https://npiregistry.cms.hhs.gov/api/"
                providers_per_request = 200  # Maximum allowed by API per request
                params = {
                    'version': '2.1',
                    'taxonomy_description': taxonomy_description,
                    'city': city,
                    'state': state,
                    'limit': providers_per_request,
                    'skip': 0
                }

                provider_data = []

                while True:
                    response = requests.get(base_url, params=params)
                    data = response.json()

                    if 'results' in data and data['results']:
                        for provider in data['results']:
                            if provider['addresses'][0]['city'].lower() == city.lower() and provider['addresses'][0]['state'].lower() == state.lower():
                                primary_taxonomy = next((tax['desc'] for tax in provider.get('taxonomies', []) if tax['primary']), None)
                                if primary_taxonomy in ['Ophthalmology', 'Optometrist']:
                                    provider_info = {
                                        'NPI': provider.get('number'),
                                        'First Name': provider.get('basic', {}).get('first_name'),
                                        'Last Name': provider.get('basic', {}).get('last_name'),
                                        'Address': provider['addresses'][0]['address_1'],
                                        'City': provider['addresses'][0]['city'],
                                        'State': provider['addresses'][0]['state'],
                                        'Postal Code': provider['addresses'][0]['postal_code'][:5],
                                        'Primary Taxonomy': primary_taxonomy
                                    }
                                    provider_data.append(provider_info)

                        params['skip'] += len(data['results'])
                    else:
                        break

                return provider_data

            def fetch_all_providers_in_city_state(city, state):
                oph_providers = fetch_providers_by_taxonomy(city, state, 'Ophthalmology')
                opt_providers = fetch_providers_by_taxonomy(city, state, 'Optometrist')

                # Combine the lists of providers into one list
                provider_data = oph_providers + opt_providers

                # Convert the combined list to a DataFrame
                df = pd.DataFrame(provider_data)

                df.sort_values(by='Primary Taxonomy', ascending=True, inplace=True)
                df = df.reset_index(drop=True)

                return df

            try:
                result = fetch_all_providers_in_city_state(city, state)

                if Taxonomy_choice == 'Ophthalmology':
                    oph_df = result[result['Primary Taxonomy'].str.contains('Ophthalmology')]
                    csv = oph_df.to_csv(index=False)

                    st.write(oph_df)
                    st.download_button(
                        label='Download CSV',
                        data=csv,
                        file_name='NPI_OPH_' + str(city) + '_' + str(state) + '.csv',
                        mime='text/csv'
                    )

                elif Taxonomy_choice == 'Optometrist':
                    opt_df = result[result['Primary Taxonomy'].str.contains('Optometrist')]
                    csv = opt_df.to_csv(index=False)

                    st.write(opt_df)
                    st.download_button(
                        label='Download CSV',
                        data=csv,
                        file_name='NPI_OPT_' + str(city) + '_' + str(state) + '.csv',
                        mime='text/csv'
                    )

                else:
                    csv = result.to_csv(index=False)
                    st.write(result)
                    st.download_button(
                        label='Download CSV',
                        data=csv,
                        file_name='NPI_OPH_OPT_' + str(city) + '_' + str(state) + '.csv',
                        mime='text/csv'
                    )

            except Exception as e:
                st.write("There was an error retrieving data for the specified city and state: " + str(e))
