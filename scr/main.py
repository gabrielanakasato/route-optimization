from params import Params
from nodes.optimization_setup import opt_setup
from nodes.route_optimization  import route_opt

if __name__ == '__main__':
    params = Params()

    depot_address, number_deliveries, deliveries_dict, depot_example, deliveries_example = opt_setup(params)
    route_opt(depot_address, number_deliveries, deliveries_dict, depot_example, deliveries_example,
              params.matrices_example)
