import streamlit as st

from params import Params
from nodes.pt_optimization_setup import opt_setup
from nodes.pt_route_optimization import route_opt

if __name__ == '__main__':
    params = Params()

    # english = st.sidebar.checkbox(label='Change the language to English')

    depot_address, number_deliveries, deliveries_dict, depot_example, deliveries_example = opt_setup(params)
    route_opt(depot_address, number_deliveries, deliveries_dict, depot_example, deliveries_example,
              params.matrices_example)
