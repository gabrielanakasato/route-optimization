# Import necessary libraries
import ast
import json
import os
import re
import time
import urllib

import folium
import pandas as pd
import streamlit as st

from dotenv import load_dotenv, find_dotenv
from folium import plugins
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from streamlit_folium import folium_static

# Necessary information
chrome_path = 'D:/dist/chromedriver.exe'

uf = ('-', 'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', ' ES', 'GO', 'MA', 'MT', 'MS', 'MG',
      'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO')

# Example of locations
locations_example = pd.read_csv('data/locations_example.csv')
matrices_example = pd.read_csv('data/matrices_example.csv')

# Convert string to list
matrices_example['dist_matrix'] = matrices_example['dist_matrix'].apply(ast.literal_eval)
matrices_example['time_matrix'] = matrices_example['time_matrix'].apply(ast.literal_eval)

# Functions


def pretty_time_delta(seconds):
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%s%dd%dh%dm%ds' % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        return '%s%dh%dm%ds' % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return '%s%dm%ds' % (sign_string, minutes, seconds)
    else:
        return '%s%ds' % (sign_string, seconds)


def input_address_depot(df_example):

    '''
    Creates and returns a dictionary with the depot's address.
    :param df_example:
    :return:
    '''

    address_dict = {}

    address_dict['name'] = st.sidebar.text_input("Digite o endereço da sua localização",
                                                 df_example.loc[df_example['place'] == 'depot', 'name'][0])
    address_dict['number'] = st.sidebar.text_input("Digite o número da sua localização",
                                                   df_example.loc[df_example['place'] == 'depot', 'number'][0])
    address_dict['uf'] = st.sidebar.selectbox("Escolha o estado da sua localização", uf,
                                              uf.index(df_example.loc[df_example['place'] == 'depot', 'uf'][0]))
    address_dict['city'] = st.sidebar.text_input("Digite a cidade da sua localização",
                                                 df_example.loc[df_example['place'] == 'depot', 'city'][0])

    # Title the strings
    address_dict['name'] = address_dict['name'].title()
    address_dict['city'] = address_dict['city'].title()

    # Create a complete address
    depot_address_complete = address_dict['name'].title() + ', ' + address_dict['number'] + ' - ' \
                             + address_dict['city'].title() + ', ' + address_dict['uf']

    if (address_dict['name'] == '') or (address_dict['number'] == '') or (address_dict['city'] == '') or \
            (address_dict['uf'] == '-'):
        st.sidebar.write('Endereço atual:')
    else:
        st.sidebar.markdown(f"Sua localização é **{depot_address_complete}**.")

    if (address_dict['name'].lower() == df_example.loc[df_example.index == 0, 'name'][0].lower()) and \
            (address_dict['number'] == str(df_example.loc[df_example.index == 0, 'number'][0])) and \
            (address_dict['uf'].lower() == df_example.loc[df_example.index == 0, 'uf'][0].lower()) and \
            (address_dict['city'].lower() == df_example.loc[df_example.index == 0, 'city'][0].lower()):

        # If the example is being used
        example = True
        address_dict['lat_lon'] = df_example.loc[df_example.index == 0, 'lat_lon'][0]
        address_dict['lat'] = df_example.loc[df_example.index == 0, 'lat'][0]
        address_dict['lon'] = df_example.loc[df_example.index == 0, 'lon'][0]
        # st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')
    else:
        # Search the coordinates on Google Maps using Selenium
        example = False
        get_depot_coordinate = st.sidebar.checkbox(f'Enviar sua localização')
        if get_depot_coordinate:
            address_dict['lat_lon'] = search_coordinates(address_dict)
            address_dict['lat'] = re.findall('-*\d+\.+\d*,', address_dict['lat_lon'])[0].replace(',', '')
            address_dict['lon'] = re.findall(',-*\d+\.+\d*', address_dict['lat_lon'])[0].replace(',', '')
            # st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')

    return address_dict, example


def search_coordinates(address_dict):
    url = 'https://www.google.com.br/maps/place/'
    address_name = address_dict['name']
    address_number = address_dict['number']
    address_uf = address_dict['uf']
    address_city = address_dict['city']
    url_complete = url + address_name.replace(' ', '+').lower() + ',+' + address_number + ',+' \
                   + address_city.replace(' ', '+').lower() + ',+' + address_uf.lower()

    # Open the Chrome browser
    chrome_options = Options()
    chrome_options.headless = True
    driver = webdriver.Chrome(executable_path=chrome_path, options=chrome_options)

    # Navigate to webpage
    driver.get(url_complete)

    # Wait 3 seconds
    time.sleep(4)

    # Save the current url in a variable (which contains the coordinates)
    updated_url = driver.current_url

    # Close the browser
    driver.close()

    # Get the coordinates in a string
    coordinates = re.findall('-*\d+\.+\d*,-*\d+\.+\d*', updated_url)[0]

    st.sidebar.markdown('**Localização recebida**')

    return coordinates


def input_address_delivery(index, df_example, depot_address: dict):

    '''
    Creates and returns a dictionary with address of the delivery location.
    :return:
    '''

    st.sidebar.subheader(f'Entrega {index}')

    address_dict = {}
    example = None

    # If the index is smaller than 13 (since the example has 12 locations)
    if index < df_example.shape[0]:
        address_dict['person'] = st.sidebar.text_input(f"Digite o nome da pessoa da Entrega {index}",
                                                       df_example.loc[df_example.index == index, 'place'][index].title())
        address_dict['name'] = st.sidebar.text_input(f"Digite o endereço da Entrega {index}",
                                                     df_example.loc[df_example.index == index, 'name'][index])
        address_dict['number'] = st.sidebar.text_input(f"Digite o número da da Entrega {index}",
                                                       df_example.loc[df_example.index == index, 'number'][index])
    else:
        address_dict['person'] = st.sidebar.text_input(f"Digite o nome da pessoa da Entrega {index}")
        address_dict['name'] = st.sidebar.text_input(f"Digite o endereço da Entrega {index}")
        address_dict['number'] = st.sidebar.text_input(f"Digite o número da da Entrega {index}")

    address_dict['uf'] = st.sidebar.selectbox(f"Escolha o estado da da Entrega {index}", uf, uf.index(depot_address['uf']))
    address_dict['city'] = st.sidebar.text_input(f"Digite a cidade da Entrega {index}", depot_address['city'])

    # Title the strings
    address_dict['name'] = address_dict['name'].title()
    address_dict['city'] = address_dict['city'].title()

    # Create a complete address
    address_complete = address_dict['name'].title() + ', ' + address_dict['number'] + ' - ' \
                       + address_dict['city'].title() + ', ' + address_dict['uf']

    # Check if the address is completed
    if (address_dict['name'] == '') or (address_dict['number'] == '') or (address_dict['city'] == '') or \
            (address_dict['uf'] == '-'):
        st.sidebar.markdown(f'Localização da Entrega {index}: - ')
    else:
        st.sidebar.markdown(f'Localização da Entrega {index} para **{address_dict["person"].title()}**: **{address_complete}**')

    # Check if the information is the same as the example

    if index < df_example.shape[0] and \
       (address_dict['name'].lower() == df_example.loc[df_example.index == index, 'name'][index].lower()) and \
       (address_dict['number'] == str(df_example.loc[df_example.index == index, 'number'][index])) and \
       (address_dict['uf'].lower() == df_example.loc[df_example.index == index, 'uf'][index].lower()) and \
       (address_dict['city'].lower() == df_example.loc[df_example.index == index, 'city'][index].lower()):

        # If the example is being used
        example = True
        address_dict['lat_lon'] = df_example.loc[df_example.index == index, 'lat_lon'][index]
        address_dict['lat'] = df_example.loc[df_example.index == index, 'lat'][index]
        address_dict['lon'] = df_example.loc[df_example.index == index, 'lon'][index]
        # st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')
    else:
        # Search the coordinates on Google Maps using Selenium
        example = False
        get_depot_coordinate = st.sidebar.checkbox(f'Enviar localização da Entrega {index}')
        if get_depot_coordinate:
            address_dict['lat_lon'] = search_coordinates(address_dict)
            address_dict['lat'] = re.findall('-*\d+\.+\d*,', address_dict['lat_lon'])[0].replace(',', '')
            address_dict['lon'] = re.findall(',-*\d+\.+\d*', address_dict['lat_lon'])[0].replace(',', '')
            # st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')


    return address_dict, example


def create_data(api_key, addresses):
    '''
    Creates the data
    '''

    data = {}

    # API Key
    data['api_key'] = api_key

    # Locations - [lat, lon]
    data['addresses'] = addresses

    return data


def request_info(origin_addresses, dest_addresses, api_key):
    '''
    Build and send request for the given origin and destination addresses
    '''

    url_beginning = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=metric'

    def build_str_addresses(addresses):
        '''
        Builds a pipe-separated string of addresses
        '''
        address_str = ''

        for index in range(len(addresses) - 1):
            address_str += addresses[index] + '|'
        address_str += addresses[-1]
        return address_str

    # Strings for origins and destinations
    origins_str = build_str_addresses(origin_addresses)
    destinations_str = build_str_addresses(dest_addresses)

    url_complete = url_beginning + '&origins=' + origins_str + '&destinations=' + destinations_str + '&key=' + api_key

    result = urllib.request.urlopen(url_complete).read()
    response = json.loads(result)

    return response


def build_matrices(response):
    '''
    Builds the distance matrix and the time matrix
    '''

    dist_matrix = []
    time_matrix = []

    for origin_address in response['rows']:
        dist_list = [origin_address['elements'][dest_address]['distance']['value']
                     for dest_address in range(len(origin_address['elements']))]

        time_list = [origin_address['elements'][dest_address]['duration']['value']
                     for dest_address in range(len(origin_address['elements']))]

        dist_matrix.append(dist_list)
        time_matrix.append(time_list)

    return dist_matrix, time_matrix


def create_matrices(data):
    '''
    Creates the distance and time matrices.
    '''

    addresses = data["addresses"]
    api_key = data["api_key"]

    # Distance Matrix API only accepts 100 elemnts per request
    max_elements = 100
    num_addresses = len(addresses)  # Example: 11
    # Maximum number of rows that can be computes per request
    max_rows = max_elements // num_addresses
    q, r = divmod(num_addresses, max_rows)  # num_addresses = q * max_rows + r (Example: q = 1 and r = 2)
    dest_addresses = addresses

    distance_matrix = []
    time_matrix = []

    # Send q requests, returning max_rows rows per request
    for index in range(q):
        origin_addresses = addresses[index * max_rows:(index + 1) * max_rows]
        response = request_info(origin_addresses=origin_addresses, dest_addresses=dest_addresses, api_key=api_key)
        distance_matrix += build_matrices(response)[0]
        time_matrix += build_matrices(response)[1]

    # Get the remaining remaining r rows, if necessary
    if r > 0:
        origin_addresses = addresses[q * max_rows:q * max_rows + r]
        response = request_info(origin_addresses=origin_addresses, dest_addresses=dest_addresses, api_key=api_key)
        distance_matrix += build_matrices(response)[0]
        time_matrix += build_matrices(response)[1]

    return distance_matrix, time_matrix


def create_data_model(number_vehicles, dist_matrix, time_matrix):
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = dist_matrix
    data['time_matrix'] = time_matrix
    data['num_vehicles'] = number_vehicles
    data['depot'] = 0
    return data


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    # st.write(f'Objective: {solution.ObjectiveValue()} seconds')
    total_time = 0
    routes_all = {}
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        st.markdown(f'Rota para o **veículo {vehicle_id + 1}**')
        route_each = []
        plan_output = ''
        route_time = 0
        max_route_time = 0
        i = 0
        while not routing.IsEnd(index):
            plan_output += f' {manager.IndexToNode(index)} ->'
            route_each.append(manager.IndexToNode(index))
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_time += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
            i += 1
        route_each.append(0)
        plan_output += f' {manager.IndexToNode(index)}'
        routes_all[vehicle_id] = route_each
        st.markdown(f'**{plan_output}**')
        st.write(f'Tempo da rota: {pretty_time_delta(route_time)}')
        total_time += route_time
        max_route_time = max(route_time, max_route_time)
    # st.markdown(f'**Total Time of all routes: {total_time} seconds**')
    st.markdown(f'**Tempo Máximo de todas as rotas: {pretty_time_delta(max_route_time)}**')

    return routes_all


def opt_setup():

    '''
    Function to run in the 'Configurações' section.
    :return:
    '''

    # TITLE
    st.sidebar.title('Configurações')

    # DEPOT
    st.sidebar.header('Sua Localização')

    depot_address, depot_example = input_address_depot(locations_example)

    # DELIVERIES
    st.sidebar.header('Entregas')

    number_deliveries = st.sidebar.number_input(label='Número de entregas', min_value=2, step=1, value=12)

    # Create a dictionary with the addresses of the delivery locations
    deliveries_dict = {}
    deliveries_example = {}

    for delivery_index in range(number_deliveries):
        deliveries_dict[delivery_index + 1], deliveries_example[delivery_index + 1] = input_address_delivery(
            (delivery_index + 1), locations_example, depot_address)

    deliveries_example = False not in deliveries_example.values()

    return depot_address, number_deliveries, deliveries_dict, depot_example, deliveries_example


def route_opt(depot_address, number_deliveries, deliveries_dict, depot_example, deliveries_example, matrices_example):

    '''

    :param depot_address:
    :param number_deliveries:
    :param deliveries_dict:
    :param depot_example:
    :param deliveries_example:
    :param matrices_example:
    :return:
    '''

    # ROUTE OPTIMIZATION
    st.title('Otimização de rotas')

    # Start Route Optimization
    number_vehicles = st.number_input(label='Número de veículos', min_value=1, step=1)
    waiting_stop = st.number_input(label='Período máximo de espera em uma parada em minutos', min_value=1, step=1,
                                   value=15)
    max_travel_time = st.number_input(label='Período máximo de uma viagem em minutos', min_value=1, step=1, value=150)

    if depot_example == True and deliveries_example == True and number_deliveries == 12:
        st.write('It IS the example.')
        # Create the matrices
        dist_matrix = [row for row in matrices_example['dist_matrix']]
        time_matrix = [row for row in matrices_example['time_matrix']]
    else:
        st.write('It is NOT the example.')
        get_matrices = st.checkbox(f'Enviar dados para otimização')

        if get_matrices:
            # Need to get the matrices
            load_dotenv(find_dotenv())
            api_key = os.getenv('google_maps_key')

            # Create a list with all addresses
            deliveries_addresses = [each_address['lat_lon']
                                    for each_address in deliveries_dict.values()]
            all_addresses = [depot_address['lat_lon']] + deliveries_addresses

            # Create the matrices for the optimization
            data = create_data(api_key=api_key, addresses=all_addresses)
            dist_matrix, time_matrix = create_matrices(data)

    begin_opt = st.button('Iniciar otimização')
    solution_found = False

    if begin_opt:

        # Instantiate the data problem.
        data = create_data_model(number_vehicles, dist_matrix, time_matrix)

        # Create the routing index manager.
        manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                               data['num_vehicles'], data['depot'])

        # Create Routing Model.
        routing = pywrapcp.RoutingModel(manager)

        # Create and register a transit callback.

        def time_callback(from_index, to_index):
            """Returns the distance between the two nodes."""
            # Convert from routing variable Index to distance matrix NodeIndex.
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['time_matrix'][from_node][to_node]

        transit_callback_index = routing.RegisterTransitCallback(time_callback)

        # Define cost of each arc.
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Add Time constraint.
        dimension_name = 'Time'
        routing.AddDimension(
            transit_callback_index,
            waiting_stop * 60,  # Maximum watiing time in each stop
            max_travel_time * 60,  # Vehicle maximum travel time
            True,  # start cumul to zero
            dimension_name)
        time_dimension = routing.GetDimensionOrDie(dimension_name)
        time_dimension.SetGlobalSpanCostCoefficient(100)

        # Setting first solution heuristic.
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

        # Solve the problem.
        solution = routing.SolveWithParameters(search_parameters)

        # Print solution on console.
        if solution:
            routes_all = print_solution(data, manager, routing, solution)
            solution_found = True
        else:
            st.write('No solution was found.')
            solution_found = False

    # Map
    # Create the map
    map_solution = folium.Map(location=[depot_address['lat'], depot_address['lon']], zoom_start=11.5)

    # List of colors
    colors = ['lightblue', 'lightgreen', 'pink', 'cadetblue', 'orange', 'purple', 'green',
              'red', 'darkblue', 'darkred', 'darkgreen', 'darkpurple', 'black', 'beige', 'lightgray']

    # Add a marker for depot's location
    folium.Marker(location=[depot_address['lat'], depot_address['lon']],
                  popup='Sua Localização',
                  tooltip=f'Sua Localização', ).add_to(map_solution)

    try:
        # Add a marker for deliveries' location
        if solution_found == False:
            for delivery in deliveries_dict:
                folium.Marker(location=[deliveries_dict[delivery]['lat'], deliveries_dict[delivery]['lon']],
                              icon=folium.Icon(color='lightgray', icon=None),
                              popup=f'''{deliveries_dict[delivery]["person"]}
{deliveries_dict[delivery]["name"]}, n°{deliveries_dict[delivery]["number"]}''',
                              tooltip=f'Entrega {delivery} - {deliveries_dict[delivery]["person"]}').add_to(
                    map_solution)
        else:
            # st.write('Solution found')
            for vehicle in routes_all:

                # Group the markers according to the vehicle
                for delivery_index in routes_all[vehicle][1:-1]:
                    folium.Marker(
                        location=[deliveries_dict[delivery_index]['lat'], deliveries_dict[delivery_index]['lon']],
                        icon=folium.Icon(color=colors[vehicle], icon=None),
                        popup=f'''{deliveries_dict[delivery_index]["person"]}
{deliveries_dict[delivery_index]["name"]}, n°{deliveries_dict[delivery_index]["number"]}''',
                        tooltip=f'Entrega {delivery_index} - {deliveries_dict[delivery_index]["person"]}').add_to(
                        map_solution)

                list_coord = []
                for delivery_index in routes_all[vehicle]:
                    if delivery_index == 0:
                        list_coord.append([depot_address['lat'], depot_address['lon']])
                    else:
                        list_coord.append(
                            [deliveries_dict[delivery_index]['lat'], deliveries_dict[delivery_index]['lon']])

                sequence = folium.PolyLine(locations=list_coord,
                                           weight=1, color=colors[vehicle], opacity=0).add_to(map_solution)

                attr = {'fill': colors[vehicle]}

                plugins.PolyLineTextPath(sequence,
                                         '\u25BA',
                                         repeat=True,
                                         offset=6,
                                         attributes=attr).add_to(map_solution)
    except:
        # If the delivery location has no coordinates
        pass

    # Show the map
    folium_static(map_solution)

# Start Streamlit
depot_address, number_deliveries, deliveries_dict, depot_example, deliveries_example = opt_setup()
route_opt(depot_address, number_deliveries, deliveries_dict, depot_example, deliveries_example, matrices_example)
