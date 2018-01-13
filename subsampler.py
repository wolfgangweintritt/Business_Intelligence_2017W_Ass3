#!/usr/bin/env python
"""Read a dataset and keep only the first X percent of it, where the distribution among classes stays the same"""

import math
import argparse

def percent_type(arg):
    """"""
    arg = float(arg)
    if arg < 0:
        raise argparse.ArgumentTypeError("Minimum percentage is 0")
    elif arg > 100:
        raise argparse.ArgumentTypeError("Maximum percentage is 100")
    return arg

description = "Reduce the size of the dataset to a given percentage."
epilog = "This script has the side-effect of sorting the dataset by classes."
parser = argparse.ArgumentParser(description=description, epilog=epilog)

parser.add_argument("-p", "--percent",
                    metavar="PERCENT",
                    help="The percentage of the dataset to keep",
                    type=percent_type,
                    default=100)

parser.add_argument("data_file",
                    metavar="DATASET",
                    help="The Dataset to reduce",
                    type=str)

args = parser.parse_args()

arff_file = args.data_file
percent = args.percent / 100

if not arff_file.endswith(".arff"):
    raise Exception("This script is too simple to handle anything else than an ARFF file!")

lines = []
output_lines = []
data = []
with open(arff_file) as file_:
    lines = file_.readlines()

# save header and data stuff separately
in_data_section = False
for line in lines:
    line = line.strip()
    if not in_data_section:
        output_lines.append(line)
        if line.startswith("@data"):
            in_data_section = True
    else:
        data.append(line)

# sort lines per output class
lines_per_class = {}
for line in data:
    values = line.split(",")
    if values[-1] not in lines_per_class.keys():
        lines_per_class[values[-1]] = []

    lines_per_class[values[-1]].append(line)

# remember only the given percentage of the lines
for key in lines_per_class.keys():
    line_count = len(lines_per_class[key])
    count_to_remember = int(math.floor(line_count * percent))
    output_lines.extend(lines_per_class[key][:count_to_remember])

# print the output
for line in output_lines:
    print(line)
