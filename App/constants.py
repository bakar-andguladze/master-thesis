import pandas as pd
import os 
import numpy as np
from prepare_test import get_packet_size

topo_size = 3

topo_caps = "data/assigned_capacities.txt"

h1_ip = "10.0.0.10"
h2_ip = "10.0.{}.10".format(topo_size)

packet_size = get_packet_size() # number of symbols in packet_data.txt 

