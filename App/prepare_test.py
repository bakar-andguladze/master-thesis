import random
import time

def generate_capacities(min, max, n_links):
    """
    Generate random capacities from [min, max] range to apply to the mininet topology
    :param min: capacity range start
    :param max: capacity range end
    :param n_links: number of links in the network
    """
    capacities = []
    for i in range(n_links):
        try:
            capacity = random.randrange(min, max)
        except ValueError:
            capacity = min
        finally:
            capacities.append(capacity)

    return capacities


def get_config_parameters():
    pass


