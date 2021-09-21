import random
import time
import json

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
    assert (packet_size > 0 and packet_size < 2000), "Packet size must be a positive number and shouldn't exceed maximum segment size"
    test_config['packet_size'] = packet_size

    # Read packets per hop
    packets_per_hop = data['packets_per_hop']
    assert packets_per_hop > 10, "There should be at least 10 packets per hop"
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

    # Read output directory
    output_dir = data['output']
    test_config['output_dir'] = output_dir

    return test_config

