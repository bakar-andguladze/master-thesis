import random
import time

def generate_capacities(min, max, n_links):
    """
    Generate random capacities from [min, max] range to apply to the mininet topology
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


"""
arr = generate_capacities(100, 150, 4)
print(arr)
"""

def parse_config():
    pass


