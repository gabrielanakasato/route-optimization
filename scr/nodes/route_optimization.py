# Import necessary libraries
import json
import os
from urllib import request

import folium
import streamlit as st
from dotenv import load_dotenv, find_dotenv
from folium import plugins
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from streamlit_folium import folium_static


def pretty_time_delta(seconds):

    """
    Converts an integer in seconds to a string representing a time delta in days, hours, minutes and seconds

    Parameters
    ----------
    seconds: int
        Seconds represented by an integer

    Returns
    -------
    time: str
        String representing a time delta in days, hours, minutes and seconds
    """

    sign_string = '-' if seconds < 0 else ''
    seconds = abs(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        time = '%s%dd%dh%dm%ds' % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        time = '%s%dh%dm%ds' % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        time = '%s%dm%ds' % (sign_string, minutes, seconds)
    else:
        time = '%s%ds' % (sign_string, seconds)

    return time


def create_data(api_key, addresses):

    """
    Creates a dictionary that contains the API key and the coordinates of the locations

    Parameters
    ----------
    api_key: str
        String that contains the Distance Matrix API key
    addresses: list
        List that contains the coordinates of the locations, including the depot's
    Returns
    -------
    data: dict
        Dictionary that contains the API key and the coordinates of the locations
    """

    data = {'api_key': api_key,
            'addresses': addresses}  # Locations - [lat, lon]

    return data


def request_info(origin_addresses, dest_addresses, api_key):

    """
    Build and send request of the given origin and destination addresses for the Distance Matrix

    Parameters
    ----------
    origin_addresses: list
        List that contains the coordinates of origin locations
    dest_addresses: list
        List that contains the coordinates of destination locations
    api_key: str
        String that contains the Distance Matrix API key

    Returns
    -------
    response: dict
        Dictionary that contains the Distance Matrix response
    """

    url_beginning = 'https://maps.googleapis.com/maps/api/distancematrix/json?units=metric'

    def build_str_addresses(addresses):

        """
        Builds a pipe-separated string of addresses

        Parameters
        ----------
        addresses: list
            List that contains the coordinates of locations

        Returns
        -------
        address_str: str
            Pipe-separated string of the coordinates of the addresses
        """

        address_str = ''

        for index in range(len(addresses) - 1):
            address_str += addresses[index] + '|'
        address_str += addresses[-1]
        return address_str

    # Strings for origins and destinations
    origins_str = build_str_addresses(origin_addresses)
    destinations_str = build_str_addresses(dest_addresses)

    url_complete = url_beginning + '&origins=' + origins_str + '&destinations=' + destinations_str + '&key=' + api_key

    result = request.urlopen(url_complete).read()
    response = json.loads(result)

    return response


def build_matrices(response):

    """
    Converts the Distance Matrix response into the distance matrix and the time travel matrix

    Parameters
    ----------
    response: dict
        Dictionary that contains the Distance Matrix response

    Returns
    -------
    dist_matrix: list
        Distance matrix (list that contains list of the distances between the origin and destination addresses)
    time_matrix: list
        Time travel matrix (list that contains list of the time travel between the origin and destination addresses)
    """

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


@st.cache(suppress_st_warning=True)
def create_matrices(data):

    """
    Makes requests to the Distance Matrix API and creates the distance and time travel matrices.

    Parameters
    ----------
    data: dict
        Dictionary that contains the API key and the coordinates of the locations

    Returns
    -------
    dist_matrix: list
        Distance matrix (list that contains list of the distances between the origin and destination addresses)
    time_matrix: list
        Time travel matrix (list that contains list of the time travel between the origin and destination addresses)
    """

    addresses = data["addresses"]
    api_key = data["api_key"]

    # Distance Matrix API only accepts 100 elements per request
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

    """
    Stores the data for the problem

    Parameters
    ----------
    number_vehicles: int
        Number of vehicles
    dist_matrix: list
        Distance matrix
    time_matrix: list
        Time travel matrix

    Returns
    -------
    data: dict
        Dictionary that contains the data for the problem
    """

    data = {'distance_matrix': dist_matrix,
            'time_matrix': time_matrix,
            'num_vehicles': number_vehicles,
            'depot': 0}

    return data


def print_solution(data, manager, routing, solution):

    """
    Prints the answer on the screen.

    Parameters
    ----------
    data: dict
        Dictionary that contains the data for the problem
    manager:
        Routing Index Manager
    routing:
        Routing Model
    solution:
        Solution of the problem

    Returns
    -------
    routes_all: list
       List containing the sequence of locations of all routes
    """

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
        st.markdown(f'Tempo da rota: **{pretty_time_delta(route_time)}**')
        total_time += route_time
        max_route_time = max(route_time, max_route_time)
    # st.markdown(f'**Total Time of all routes: {total_time} seconds**')
    st.markdown(f'**Tempo Máximo de todas as rotas: {pretty_time_delta(max_route_time)}**')

    return routes_all


def route_opt(depot_address, number_deliveries, deliveries_dict, depot_example, deliveries_example, matrices_example):

    """
    Function to run in the main section and show the results, including the best route for each vehicle and a map.

    Parameters
    ----------
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
    matrices_example: Pandas DataFrame
        Dataframe containing the example of the distance and time travel matrices

    Returns
    -------

    """

    # ROUTE OPTIMIZATION
    st.title('Otimização de rotas')

    # Start Route Optimization
    number_vehicles = st.number_input(label='Número de veículos', min_value=1, step=1)
    waiting_stop = st.number_input(label='Período máximo de espera em uma parada em minutos', min_value=1, step=1,
                                   value=15)
    max_travel_time = st.number_input(label='Período máximo de uma viagem em minutos', min_value=1, step=1, value=150)

    if depot_example and deliveries_example and number_deliveries == 12:
        # st.write('It IS the example.')
        # Create the matrices
        dist_matrix = [row for row in matrices_example['dist_matrix']]
        time_matrix = [row for row in matrices_example['time_matrix']]
    else:
        # st.write('It is NOT the example.')
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

        # Instantiate the data problem
        data = create_data_model(number_vehicles, dist_matrix, time_matrix)

        # Create the routing index manager
        manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                               data['num_vehicles'], data['depot'])

        # Create Routing Model
        routing = pywrapcp.RoutingModel(manager)

        # Create and register a transit callback
        def time_callback(from_index, to_index):

            """
            Returns the distance between two nodes.

            Parameters
            ----------
            from_index: int
                Index of the origin address
            to_index:int
                Index of the destination address

            Returns
            -------
            data['time_matrix'][from_node][to_node]: int
                Time travel of the route from the origin address to the destination address
            """

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

    # List of colors
    colors = ['darkred', 'green', 'pink', 'orange', 'purple', 'cadetblue', 'darkgreen',
              'darkblue', 'red', 'lightblue', 'lightgreen', 'darkpurple', 'black', 'beige', 'lightgray']

    try:
        # Create the map
        map_solution = folium.Map(location=[depot_address['lat'], depot_address['lon']], zoom_start=11.5)

        # Add a marker for depot's location
        folium.Marker(location=[depot_address['lat'], depot_address['lon']],
                      popup='Sua Localização',
                      tooltip=f'Sua Localização', ).add_to(map_solution)

        # Add a marker for deliveries' location
        if not solution_found:
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
        # Show the map
        folium_static(map_solution)

    except SyntaxError:
        # If the location has no coordinates
        # Show the map
        folium_static(map_solution)
    except KeyError:
        pass
