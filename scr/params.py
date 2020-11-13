import ast

import pandas as pd


class Params:
    """
    Required parameters in this project.
    """

    # Languages
    current_lan = 'EN'
    available_lang = ('EN', 'PT')

    # List of states in Brazil
    uf = ('-', 'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', ' ES', 'GO', 'MA', 'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE',
          'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO')

    # Example
    locations_example = pd.read_csv('https://raw.githubusercontent.com/gabrielanakasato/route-optimization/main/data/locations_example.csv')
    matrices_example = pd.read_csv('https://raw.githubusercontent.com/gabrielanakasato/route-optimization/main/data/matrices_example.csv')

    matrices_example['dist_matrix'] = matrices_example['dist_matrix'].apply(ast.literal_eval)  # Convert string to list
    matrices_example['time_matrix'] = matrices_example['time_matrix'].apply(ast.literal_eval)  # Convert string to list

    # Path of the Chrome driver
    chrome_path = './chromedriver.exe'

    # Google Maps url
    maps_url = 'https://www.google.com.br/maps/place/'
