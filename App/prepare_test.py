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

    # Read capacity distribution step value
    capacity_delta = data['capacity_delta']
    assert capacity_delta > 0, "Capacity delta must be a positive number!"

    # Read measurement duration in seconds
    duration = data['duration']
    assert duration > 0, "Duration must be a positive number!"
    ret['duration'] = data['duration']


    # Read amount of cross traffic load
    try:
        ret['cross_traffic'] = data['cross_traffic']
    except KeyError:
        # No parameter given, assume cross traffic load = 1
        ret['cross_traffic'] = 1

    # Read optional packet size
    try:
        ret['packet_size'] = data['packet_size']
    except KeyError:
        # No parameter given, use default Ethernet + IP + MSS size of 1515
        ret['packet_size'] = 1515


    # Calculate random capacities for all links
    if bottleneck_location is None:
        # Random bottleneck location
        ret['capacities'] = get_capacity_distribution(capacity_range, capacity_delta, switch_count)
    else:
        # Defined bottleneck location
        ret['capacities'] = get_capacity_distribution([capacity_range[0] + capacity_delta, capacity_range[1]],
                                                      capacity_delta, switch_count)
        ret['capacities'][bottleneck_location] = capacity_range[0]
    # Set bottleneck value to minimum capacity value in link distribution
    ret['bottleneck'] = min(ret['capacities'])

    # Declare optional output file to append results to
    try:
        ret['output'] = data['output']
    except KeyError:
        ret['output'] = None

    # Return dict
    return ret


# set_packet_size(1400)
