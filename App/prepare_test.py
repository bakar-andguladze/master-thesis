import random
import time

def generate_capacities(min, max, n_links, capacity_delta=5):
    """
    Generate random capacities from [min, max] range to apply to the mininet topology
    :param min: capacity range start
    :param max: capacity range end
    :param n_links: number of links in the network
    """
    capacities = []
    for i in range(n_links):
        try:
            capacity = random.randrange(min, max, capacity_delta) 
        except ValueError:
            capacity = min
        finally:
            capacities.append(capacity)

    return capacities

def set_packet_size(size):
    f = open("data/packet_data.txt", "w")
    for i in range(size):
        f.write("A")
    f.close()

def get_packet_size():
    f = open("data/packet_data.txt", "r")
    packet = f.read()
    f.close()
    return len(packet)


def get_config_parameters():
    pass


# set_packet_size(1400)


print(get_packet_size())