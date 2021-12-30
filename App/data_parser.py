import csv
import sys

# filename = sys.argv[1]
csv_header = "path; estimated; expected; error\n"

def parse_file(filename, csv_header):
    """
    A helper function to parse raw data from experiments and convert them to csv
    """
    a_file = open(filename, "r")

    lines = a_file.readlines()
    a_file.close()

    new_file = open(filename, "w")
    new_file.write(csv_header)
    for line in lines:
        if line.startswith('(') and line.find('-1') == -1: 
            line = line.replace(" ->", ";")
            line = line.replace("%", "")
            new_file.write(line)

    new_file.close()

for i in range(1, len(sys.argv)):
    filename = sys.argv[i]
    parse_file(filename, csv_header)


