# Import required libraries
from re import findall
from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import streamlit as st


def search_coordinates(params, address_dict):

    """
    Searches the coordinates of an address using the Google Maps.

    Parameters
    ----------
    params: class
        Required parameters
    address_dict: dict
        Dictionary that contains the data about a location

    Returns
    -------
    coordinates: str
        String that contains the coordinates of the location
    """

    # Required variables
    url = params.maps_url
    address_name = address_dict['name']
    address_number = address_dict['number']
    address_uf = address_dict['uf']
    address_city = address_dict['city']
    url_complete = url + address_name.replace(' ', '+').lower() + ',+' + address_number + ',+' \
                       + address_city.replace(' ', '+').lower() + ',+' + address_uf.lower()

    # Open the Chrome browser
    chrome_options = Options()
    chrome_options.headless = True
    driver = webdriver.Chrome(executable_path=params.chrome_path, options=chrome_options)

    # Navigate to webpage
    driver.get(url_complete)

    # Wait 3 seconds
    sleep(4)

    # Save the current url in a variable (which contains the coordinates)
    updated_url = driver.current_url

    # Close the browser
    driver.close()

    # Get the coordinates in a string
    coordinates = findall("-*\d+\.+\d*,-*\d+\.+\d*", updated_url)[0]

    # Print the massage on the screen
    st.sidebar.markdown('**Localização recebida**')

    return coordinates


class InputAddresses:

    def depot(self, params):

        """
        Creates a dictionary with the depot's address information and checks if the data used is from the example
        dataframe.

        Parameters
        ----------
        params: class
            Required parameters

        Returns
        -------
        address_dict: dict
            Dictionary that contains the data about the depot's location
        example: bool
            Returns True if data of the depot's location is from the example dataframe
        """

        address_dict = {'name': st.sidebar.text_input(label="Digite o endereço da sua localização",
                                                      value=params.locations_example.loc[
                                                          params.locations_example['place'] == 'depot',
                                                          'name'][0]).strip(),
                        'number': st.sidebar.text_input(label="Digite o número da sua localização",
                                                        value=params.locations_example.loc[
                                                            params.locations_example['place'] == 'depot',
                                                            'number'][0]).strip(),
                        'uf': st.sidebar.text_input(label="Digite a sigla do estado da sua localização",
                                                    value=params.locations_example.loc[
                                                        params.locations_example['place'] == 'depot',
                                                        'uf'][0]).strip(),
                        'city': st.sidebar.text_input(label="Digite a cidade da sua localização",
                                                      value=params.locations_example.loc[
                                                          params.locations_example['place'] == 'depot',
                                                          'city'][0]).strip()}

        # Standardize the strings
        address_dict['name'] = address_dict['name'].title()
        address_dict['city'] = address_dict['city'].title()
        address_dict['uf'] = address_dict['uf'].upper()

        # Create a complete address
        depot_address_complete = address_dict['name'].title() + ', ' + address_dict['number'] + ' - ' \
                                                              + address_dict['city'].title() + ', ' + address_dict['uf']

        if (address_dict['name'] == '') or (address_dict['number'] == '') or (address_dict['city'] == '') or \
                (address_dict['uf'] == '-'):
            st.sidebar.write('Endereço atual:')
        else:
            st.sidebar.markdown(f"Sua localização é **{depot_address_complete}**.")

        if (address_dict['name'].lower() == params.locations_example.loc[params.locations_example.index == 0,
                                                                         'name'][0].lower()) and \
                (address_dict['number'] == str(params.locations_example.loc[params.locations_example.index == 0,
                                                                            'number'][0])) and \
                (address_dict['uf'].lower() == params.locations_example.loc[params.locations_example.index == 0,
                                                                            'uf'][0].lower()) and \
                (address_dict['city'].lower() == params.locations_example.loc[params.locations_example.index == 0,
                                                                              'city'][0].lower()):

            # If the example is being used
            example = True
            address_dict['lat_lon'] = params.locations_example.loc[params.locations_example.index == 0, 'lat_lon'][0]
            address_dict['lat'] = params.locations_example.loc[params.locations_example.index == 0, 'lat'][0]
            address_dict['lon'] = params.locations_example.loc[params.locations_example.index == 0, 'lon'][0]
            # st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')
        else:
            # Search the coordinates on Google Maps using Selenium
            example = False
            get_depot_coordinate = st.sidebar.checkbox(f'Enviar sua localização')

            if get_depot_coordinate:
                address_dict['lat_lon'] = search_coordinates(params, address_dict)
                address_dict['lat'] = float(findall('-*\d+\.+\d*,', address_dict['lat_lon'])[0].replace(',', ''))
                address_dict['lon'] = float(findall(',-*\d+\.+\d*', address_dict['lat_lon'])[0].replace(',', ''))
                # st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')

        return address_dict, example

    def deliveries(self, index, params, depot_address):

        """
        Creates a dictionary with a location information and checks if the data used is from the example dataframe.

        Parameters
        ----------
        params: class
            Required parameters
        index: int
            Number of deliveries
        depot_address: dict
           Dictionary that contains the data about the depot's location

        Returns
        -------
        address_dict: dict
            Dictionary that contains the data about the location
        example: bool
            Returns True if the data of the location is from the example dataframe
        """

        # Title for the delivery
        st.sidebar.subheader(f'Entrega {index}')

        address_dict = {}

        # If the number of deliveries is smaller than 13 (since the example has only 12 locations)
        if index < params.locations_example.shape[0]:
            address_dict['person'] = st.sidebar.text_input(label=f"Digite o nome da pessoa da Entrega {index}",
                                                           value=params.locations_example.loc[
                                                               params.locations_example.index == index,
                                                               'place'][index].title()).strip()
            address_dict['name'] = st.sidebar.text_input(label=f"Digite o endereço da Entrega {index}",
                                                         value=params.locations_example.loc[
                                                             params.locations_example.index == index,
                                                             'name'][index]).strip()
            address_dict['number'] = st.sidebar.text_input(label=f"Digite o número da da Entrega {index}",
                                                           value=params.locations_example.loc[
                                                               params.locations_example.index == index,
                                                               'number'][index]).strip()
        else:
            address_dict['person'] = st.sidebar.text_input(label=f"Digite o nome da pessoa da Entrega {index}").strip()
            address_dict['name'] = st.sidebar.text_input(label=f"Digite o endereço da Entrega {index}").strip()
            address_dict['number'] = st.sidebar.text_input(label=f"Digite o número da da Entrega {index}").strip()

        # As default, the city and uf will be the same as the depot's location
        address_dict['uf'] = st.sidebar.text_input(label=f"Digite a sigla do estado da Entrega {index}",
                                                   value=depot_address['uf']).strip()
        address_dict['city'] = st.sidebar.text_input(label=f"Digite a cidade da Entrega {index}",
                                                     value=depot_address['city']).strip()

        # Standardize the strings
        address_dict['name'] = address_dict['name'].title()
        address_dict['city'] = address_dict['city'].title()
        address_dict['uf'] = address_dict['uf'].upper()

        # Create a complete address
        address_complete = address_dict['name'].title() + ', ' + address_dict['number'] + ' - ' \
                                                        + address_dict['city'].title() + ', ' + address_dict['uf']

        # Check if the address is completed
        if (address_dict['name'] == '') or (address_dict['number'] == '') or (address_dict['city'] == '') or \
                (address_dict['uf'] == '-'):
            st.sidebar.markdown(f'Localização da Entrega {index}: - ')
        else:
            st.sidebar.markdown(
                f'Localização da Entrega {index} para **{address_dict["person"].title()}**: **{address_complete}**')

        # Check if the information is the same as the example

        # If the number of deliveries is smaller than 13 (since the example has only 12 locations) and
        # the example is being used
        if index < params.locations_example.shape[0] and \
                (address_dict['name'].lower() == params.locations_example.loc[params.locations_example.index == index,
                                                                              'name'][index].lower()) and \
                (address_dict['number'] == str(params.locations_example.loc[params.locations_example.index == index,
                                                                            'number'][index])) and \
                (address_dict['uf'].lower() == params.locations_example.loc[params.locations_example.index == index,
                                                                            'uf'][index].lower()) and \
                (address_dict['city'].lower() == params.locations_example.loc[params.locations_example.index == index,
                                                                              'city'][index].lower()):

            example = True
            address_dict['lat_lon'] = params.locations_example.loc[params.locations_example.index == index,
                                                                   'lat_lon'][index]
            address_dict['lat'] = params.locations_example.loc[params.locations_example.index == index, 'lat'][index]
            address_dict['lon'] = params.locations_example.loc[params.locations_example.index == index, 'lon'][index]
            # st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')
        else:
            # Search the coordinates on Google Maps using Selenium
            example = False
            get_depot_coordinate = st.sidebar.checkbox(f'Enviar localização da Entrega {index}')
            if get_depot_coordinate:
                address_dict['lat_lon'] = search_coordinates(params, address_dict)
                address_dict['lat'] = float(findall('-*\d+\.+\d*,', address_dict['lat_lon'])[0].replace(',', ''))
                address_dict['lon'] = float(findall(',-*\d+\.+\d*', address_dict['lat_lon'])[0].replace(',', ''))
                # st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')

        return address_dict, example


def opt_setup(params):

    """
    Function to run in the 'Configurações' section.

    Parameters
    ----------

    Returns
    -------
    depot_address: dict
        Data about the depot's location
    number_deliveries: int
        Number of deliveries
    deliveries_dict: dict
        Data about the deliveries' locations
    depot_example: bool
        Returns True if the data of the depot's location is from the example dataframe
    deliveries_example: bool
        Returns True if the data of the location is from the example dataframe
    """

    # TITLE
    st.sidebar.markdown('<h1><u>Configurações</u></h1>', unsafe_allow_html=True)

    input_address = InputAddresses()

    # DEPOT
    st.sidebar.header('Sua Localização')

    depot_address, depot_example = input_address.depot(params)

    # DELIVERIES
    st.sidebar.header('Entregas')

    number_deliveries = st.sidebar.number_input(label='Número de entregas', min_value=2, step=1, value=12)

    # Create a dictionary with the addresses of the delivery locations
    deliveries_dict = {}
    deliveries_example = {}

    for delivery_index in range(number_deliveries):
        deliveries_dict[delivery_index + 1], deliveries_example[delivery_index + 1] = input_address.deliveries(
            (delivery_index + 1), params, depot_address)

    deliveries_example = False not in deliveries_example.values()

    return depot_address, number_deliveries, deliveries_dict, depot_example, deliveries_example
