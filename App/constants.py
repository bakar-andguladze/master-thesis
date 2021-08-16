import pandas as pd
import os 
import numpy as np

topo_size = 3

max_difference = 1.0

topo_caps = "outputs/assigned_capacities.txt"

h1_ip = "10.0.0.10"
h2_ip = "10.0.{}.10".format(topo_size)

