# Import necessary libraries
import ast
import json
import os
import re
import requests
import time
import urllib

import folium
import pandas as pd
import numpy as np
import streamlit as st

from dotenv import load_dotenv, find_dotenv
from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from streamlit_folium import folium_static

# TITLE
st.title('Otimizador de Rotas')

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

# DEPOT
st.header('Sua Localização')


def input_address_depot(df_example):

    '''
    Creates and returns a dictionary with the depot's address.
    :param df_example:
    :return:
    '''

    address_dict = {}

    address_dict['name'] = st.text_input("Digite o endereço da sua localização",
                                         df_example.loc[df_example['place'] == 'depot', 'name'][0])
    address_dict['number'] = st.text_input("Digite o número da sua localização",
                                           df_example.loc[df_example['place'] == 'depot', 'number'][0])
    address_dict['uf'] = st.selectbox("Escolha o estado da sua localização", uf,
                                      uf.index(df_example.loc[df_example['place'] == 'depot', 'uf'][0]))
    address_dict['city'] = st.text_input("Digite a cidade da sua localização",
                                         df_example.loc[df_example['place'] == 'depot', 'city'][0])

    # Title the strings
    address_dict['name'] = address_dict['name'].title()
    address_dict['city'] = address_dict['city'].title()

    # Create a complete address
    depot_address_complete = address_dict['name'].title() + ', ' + address_dict['number'] + ' - ' \
                             + address_dict['city'].title() + ', ' + address_dict['uf']

    if (address_dict['name'] == '') or (address_dict['number'] == '') or (address_dict['city'] == '') or \
            (address_dict['uf'] == '-'):
        st.write('Endereço atual:')
    else:
        st.markdown(f"Sua localização é **{depot_address_complete}**.")

    if (address_dict['name'].lower() == df_example.loc[df_example.index == 0, 'name'][0].lower()) and \
            (address_dict['number'] == str(df_example.loc[df_example.index == 0, 'number'][0])) and \
            (address_dict['uf'].lower() == df_example.loc[df_example.index == 0, 'uf'][0].lower()) and \
            (address_dict['city'].lower() == df_example.loc[df_example.index == 0, 'city'][0].lower()):

        # If the example is being used
        address_dict['lat_lon'] = df_example.loc[df_example.index == 0, 'lat_lon'][0]
        address_dict['lat'] = df_example.loc[df_example.index == 0, 'lat'][0]
        address_dict['lon'] = df_example.loc[df_example.index == 0, 'lon'][0]
        st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')
    else:
        # Search the coordinates on Google Maps using Selenium
        get_depot_coordinate = st.checkbox(f'Enviar sua localização')
        if get_depot_coordinate:
            address_dict['lat_lon'] = search_coordinates(address_dict)
            address_dict['lat'] = re.findall('-*\d+\.+\d*,', address_dict['lat_lon'])[0].replace(',', '')
            address_dict['lon'] = re.findall(',-*\d+\.+\d*', address_dict['lat_lon'])[0].replace(',', '')
            st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')

    return address_dict


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

    st.markdown('**Localização recebida**')

    return coordinates


depot_address = input_address_depot(locations_example)
st.write(depot_address)

# DELIVERIES
st.header('Entregas')



def input_address_delivery(index, df_example):

    '''
    Creates and returns a dictionary with address of the delivery location.
    :return:
    '''

    st.subheader(f'Entrega {index}')

    address_dict = {}

    if index < df_example.shape[0]:
        address_dict['name'] = st.text_input(f"Digite o endereço da Entrega {index}",
                                             df_example.loc[df_example.index == index, 'name'][index])
        address_dict['number'] = st.text_input(f"Digite o número da da Entrega {index}",
                                               df_example.loc[df_example.index == index, 'number'][index])
        address_dict['uf'] = st.selectbox(f"Escolha o estado da da Entrega {index}", uf,
                                          uf.index(df_example.loc[df_example.index == index, 'uf'][index]))
        address_dict['city'] = st.text_input(f"Digite a cidade da Entrega {index}",
                                             df_example.loc[df_example.index == index, 'city'][index])
    else:
        address_dict['name'] = st.text_input(f"Digite o endereço da Entrega {index}")
        st.write('name OK')
        address_dict['number'] = st.text_input(f"Digite o número da da Entrega {index}")
        address_dict['uf'] = st.selectbox(f"Escolha o estado da da Entrega {index}", uf)
        address_dict['city'] = st.text_input(f"Digite a cidade da Entrega {index}")

    # Title the strings
    address_dict['name'] = address_dict['name'].title()
    address_dict['city'] = address_dict['city'].title()

    # Create a complete address
    address_complete = address_dict['name'].title() + ', ' + address_dict['number'] + ' - ' \
                       + address_dict['city'].title() + ', ' + address_dict['uf']

    if (address_dict['name'] == '') or (address_dict['number'] == '') or (address_dict['city'] == '') or \
            (address_dict['uf'] == '-'):
        st.write(f'Localização da Entrega {index}: - ')
    else:
        st.markdown(f'Localização da Entrega {index}: **{address_complete}**')

    if (address_dict['name'].lower() == df_example.loc[df_example.index == index, 'name'][index].lower()) and \
            (address_dict['number'] == str(df_example.loc[df_example.index == index, 'number'][index])) and \
            (address_dict['uf'].lower() == df_example.loc[df_example.index == index, 'uf'][index].lower()) and \
            (address_dict['city'].lower() == df_example.loc[df_example.index == index, 'city'][index].lower()):

        # If the example is being used
        address_dict['lat_lon'] = df_example.loc[df_example.index == index, 'lat_lon'][index]
        address_dict['lat'] = df_example.loc[df_example.index == index, 'lat'][index]
        address_dict['lon'] = df_example.loc[df_example.index == index, 'lon'][index]
        st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')
    else:
        # Search the coordinates on Google Maps using Selenium
        get_depot_coordinate = st.checkbox(f'Enviar localização da Entrega {index}')
        if get_depot_coordinate:
            address_dict['lat_lon'] = search_coordinates(address_dict)
            address_dict['lat'] = re.findall('-*\d+\.+\d*,', address_dict['lat_lon'])[0].replace(',', '')
            address_dict['lon'] = re.findall(',-*\d+\.+\d*', address_dict['lat_lon'])[0].replace(',', '')
            st.markdown(f'Coordenadas: {address_dict["lat"]}, {address_dict["lon"]}')

    return address_dict


number_deliveries = st.number_input(label='Número de entregas', min_value=2, step=1, value=12)

# Create a dictionary with the addresses of the delivery locations
deliveries_dict = {delivery_index + 1: input_address_delivery((delivery_index + 1), locations_example)
                   for delivery_index in range(number_deliveries)}

# ROUTE OPTIMIZATION
st.header('Otimização de rotas')

# Start Route Optimization
begin_opt = st.button('Iniciar otimização')


def create_data_model():
    """Stores the data for the problem."""
    data = {}
    data['distance_matrix'] = dist_matrix
    data['time_matrix'] = time_matrix
    data['num_vehicles'] = 3
    data['depot'] = 0
    return data


def print_solution(data, manager, routing, solution):
    """Prints solution on console."""
    st.write(f'Objective: {solution.ObjectiveValue()} seconds')
    total_time = 0
    for vehicle_id in range(data['num_vehicles']):
        index = routing.Start(vehicle_id)
        plan_output = f'Route for vehicle {vehicle_id}:\n'
        route_time = 0
        while not routing.IsEnd(index):
            plan_output += f' {manager.IndexToNode(index)} ->'
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_time += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id)
        plan_output += f' {manager.IndexToNode(index)}\n'
        plan_output += f'Time of the route: {route_time} seconds\n'
        st.write(plan_output)
        total_time += route_time
    st.write(f'Total Time of all routes: {total_time} seconds')


if begin_opt:
    # Create the matrices
    dist_matrix = [row for row in matrices_example['dist_matrix']]
    time_matrix = [row for row in matrices_example['time_matrix']]

    # Instantiate the data problem.
    # [START data]
    data = create_data_model()
    # [END data]

    # Create the routing index manager.
    # [START index_manager]
    manager = pywrapcp.RoutingIndexManager(len(data['time_matrix']),
                                           data['num_vehicles'], data['depot'])
    # [END index_manager]

    # Create Routing Model.
    # [START routing_model]
    routing = pywrapcp.RoutingModel(manager)


    # [END routing_model]

    # Create and register a transit callback.
    # [START transit_callback]
    def time_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['time_matrix'][from_node][to_node]


    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    # [END transit_callback]

    # Define cost of each arc.
    # [START arc_cost]
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    # [END arc_cost]

    # Add Time constraint.
    dimension_name = 'Time'
    routing.AddDimension(
        transit_callback_index,
        15 * 60,  #
        150 * 60,  # vehicle maximum travel time
        True,  # start cumul to zero
        dimension_name)
    time_dimension = routing.GetDimensionOrDie(dimension_name)
    time_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    # [START parameters]
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    # [END parameters]

    # Solve the problem.
    # [START solve]
    solution = routing.SolveWithParameters(search_parameters)
    # [END solve]

    # Print solution on console.
    # [START print_solution]
    if solution:
        print_solution(data, manager, routing, solution)
    # [END print_solution]
    else:
        st.write('No solution was found.')
