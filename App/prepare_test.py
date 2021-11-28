import random
import time
import json

from numpy.lib.npyio import save

topo_caps = "data/assigned_capacities.txt"

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
    
    # capacities = sorted(capacities, reverse=True)
    save_capacities_to_file(capacities, topo_caps)
    return capacities

def save_capacities_to_file(capacities, file=topo_caps):
    textfile = open(file, "w")
    for element in capacities:
        textfile.write(str(element) + "\n")
    textfile.close()

def set_packet_size(size):
    f = open("data/packet_data.txt", "w")
    for i in range(size - 40): 
        f.write("A")
    f.close()

def get_packet_size():
    f = open("data/packet_data.txt", "r")
    packet = f.read()
    f.close()
    return len(packet) + 40

def get_config_parameters(args):
    """
    Process json configuration file and create parameter dict for test topology
    :param args: ArgumentParser object passed from main function
    :return: dict containing parameters for testing topology 
    (c) Brzoza
    """
    # Result folder structure: config filename + current time stamp
    test_config = {'folder_name': args.config.replace('.json', '') + str(int(time.time()))}

    # Read json file
    try:
        with open(args.config) as json_file:
            data = json.load(json_file)
    except ValueError:
        print('Invalid input json file!')

    # Number of routers in a topology
    topo_size = data['topo_size']
    assert topo_size > 0, "Number of routers must be a positive number!"
    test_config['topo_size'] = topo_size

    # Read capacity distribution range
    capacity_range = data['capacity_range']
    assert len(capacity_range) == 2, "Capacity range must be an interval of two numbers!"
    test_config['capacity_range'] = capacity_range

    # Read capacity distribution step value
    capacity_delta = data['capacity_delta']
    assert capacity_delta > 0, "Capacity delta must be a positive number!"
    test_config['capacity_delta'] = capacity_delta

    # Read packet size
    packet_size = data['packet_size']
    assert (packet_size > 0 and packet_size <= 1500), "Packet size must be a positive number and shouldn't exceed maximum transmission unit (MTU)"
    test_config['packet_size'] = packet_size

    # Read packets per hop
    packets_per_hop = data['packets_per_hop']
    assert packets_per_hop >= 2, "There should be at least 2 packets per hop"
    test_config['packets_per_hop'] = packets_per_hop

    # Read icmp_ratemask
    icmp_ratelimit = data['icmp_ratelimit']
    test_config['icmp_ratelimit'] = icmp_ratelimit

    # Read packet loss
    packet_loss = data['packet_loss']
    test_config['packet_loss'] = packet_loss

    # Read cross_traffic
    cross_traffic = data['cross_traffic']
    test_config['cross_traffic'] = cross_traffic

    # Number of test runs
    repeat_test = data['repeat_test']
    test_config['repeat_test'] = repeat_test

    return test_config

