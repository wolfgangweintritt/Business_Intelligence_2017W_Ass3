#!/usr/bin/env python
"""Take a dataset and forget some of its values.

This script is called Mathias because it takes a while and then kind of forgets part of its input
"""

import argparse
import random
import math
import sys


def percentage_type(arg):
    """Check if the argument is a valid percentage between 0 and 100 inclusively"""
    arg = float(arg)
    if arg < 0:
        raise argparse.ArgumentTypeError("Minimum percentage is 0%")
    elif arg > 100:
        raise argparse.ArgumentTypeError("Maximum percentage is 100%")
    return arg


def output_type(arg):
    """Check if we support the output type supported (CSV or ARFF)"""
    arg = str(arg).lower()
    if arg not in ["csv", "arff"]:
        raise argparse.ArgumentTypeError("Only CSV and ARFF are supported")

    return arg

def parse_args():
    """Parse the command-line arguments for the script"""

    description = "'Forget' some values from the dataset and replace them by missing values."

    epilog = "This script is named Mathias because it takes a while " \
             "and then kind of forgets parts of its input."

    parser = argparse.ArgumentParser(description=description,
                                     epilog=epilog)

    parser.add_argument("-s", "--seed",
                        metavar="SEED",
                        type=int,
                        help="The Seed for the Random Number Generator",
                        default=None)

    parser.add_argument("-a", "--attributes",
                        metavar="ATTRIBUTES",
                        type=str,
                        help="Comma-separated list of attributes whose values to forget -- " \
                             "if this parameter is left out, all attributes will be affected",
                        default=None)

    parser.add_argument("-p", "--percentage",
                        metavar="PERCENT",
                        type=percentage_type,
                        help="Percentage of attributes to forget (0 <= X <= 100)",
                        required=True,
                        default=0.0)

    parser.add_argument("-c", "--missing-character",
                        metavar="CHAR",
                        type=str,
                        help="Character (or string) to use for marking that the entry is missing",
                        default="\"?\"")

    parser.add_argument("-o", "--output-file",
                        metavar="OUT-FILE",
                        help="Name of the file to store the result",
                        default=None)

    parser.add_argument("-t", "--output-type",
                        metavar="TYPE",
                        help="Type to use for the output file",
                        type=output_type,
                        default="csv")

    parser.add_argument("data_file",
                        metavar="DATASET",
                        type=str,
                        help="The dataset to use",
                        default="wall-robot-navigation")

    return parser.parse_args()


def determine_file_type(file_name):
    """Use a simple heuristic to determine the type of the specified file"""
    ext = None
    if "." in data_file:
        ext = data_file.split(".")[-1]
    else:
        ext = "arff"

    return ext


def fetch_meta_information_arff(lines):
    """Fetch the meta data from the ARFF file"""
    data = []
    for line in lines:
        data.append(line)

        # the line starting with @data is the last line we want
        if "@data" in line:
            break

    data = [l.strip() for l in data]
    return data


def fetch_data_arff(lines):
    """Fetch the data from an ARFF format file"""
    # look for the "@data" line and only take lines after this one
    data = []
    idx = -1
    for line in lines:
        idx += 1
        if "@data" in line:
            idx += 1
            break

    # strip the lines in order to get rid of newlines, etc.
    data = [l.strip() for l in lines[idx:]]

    # make the list of lines into a matrix of values
    data = [d.split(",") for d in data]

    return data


def fetch_header_arff(lines):
    """Fetch the attributes from an ARFF format file"""
    attributes = []
    for line in lines:
        line = line.strip()
        if "@attribute" in line:
            attr = line.split()[1]
            attributes.append(attr)
        elif "@data" in line:
            break

    return attributes


def fetch_data_csv(lines):
    """Fetch the data from a CSV format file"""
    # forget the first line, which should only contain strings and
    # do the same stuff as in fetch_data_arff
    data = [l.strip().split(",") for l in lines[1:]]
    return data


def fetch_header_csv(lines):
    """Fetch the attributes from a CSV format file"""
    header = lines[0].strip().split(",")
    attributes = []
    for attr in header:
        if attr.startswith("\""):
            attr = attr[1:]
        if attr.endswith("\""):
            attr = attr[:-1]
        attributes.append(attr)

    return attributes


def make_data_frame(header, body):
    """Make the lines into a data_frame"""
    data_frame = {}
    for attrib in header:
        data_frame[attrib] = []

    for line in body:
        for (idx, attrib) in enumerate(header):
            data_frame[attrib].append(line[idx])

    return data_frame


def make_lines_csv(header, data_frame):
    """Make the data_frame into lines with CSV format"""
    header_ = []
    lines = []
    line_count = 0
    for attr in header:
        header_.append("\"%s\"" % attr)
        line_count = len(data_frame[attr])

    lines.append(",".join(header_))

    for i in range(line_count):
        line = []
        for attr in hdr:
            value = data_frame[attr][i]
            line.append(value)
        lines.append(",".join(line))

    return lines


def make_lines_arff(meta, header, data_frame):
    """Make the data_frame into lines with ARFF format"""
    lines = meta[:]
    line_count = 0

    for attr in header:
        line_count = len(data_frame[attr])

    for i in range(line_count):
        line = []
        for attr in hdr:
            value = data_frame[attr][i]
            line.append(value)
        lines.append(",".join(line))

    return lines


def make_lines(header, data_frame, meta=None):
    """Make the data_frame into lines with the format read from the command-line arguments"""

    if out_file_type == "csv":
        return make_lines_csv(header, data_frame)

    elif out_file_type == "arff":
        # if we have no ARFF meta data, we have to come up with some... TODO
        if meta is None:
            raise Exception("We currently only support ARFF output if there was ARFF input")
            meta = []

        return make_lines_arff(meta, header, data_frame)

    else:
        raise Exception("Unknown Output File Format! We only know CSV and ARFF")


def fetch_data(file_name):
    """Fetch the data from a file with name file_name, dynamically deciding which method to use"""
    lines = []
    ext = determine_file_type(file_name)

    with open(file_name) as data:
        lines = data.readlines()

    # check the file extension and base the method for fetching data on it
    if ext.lower() == "csv":
        header = fetch_header_csv(lines)
        body = fetch_data_csv(lines)
    elif ext.lower() == "arff":
        global arff_meta
        arff_meta = fetch_meta_information_arff(lines)
        header = fetch_header_arff(lines)
        body = fetch_data_arff(lines)
    else:
        raise Exception("Unkonwn File Format! We only know CSV (.csv) or ARFF (.arff or no file extension)")

    # in order to preserve the original ordering of the columns, we return the header additionally
    return (header, make_data_frame(header, body))


def forget(column, percent):
    """Forget a specified percentage of the specified column"""
    if percent <= 0.5:
        # if we want to forget at most half of the dataset,
        # just go on and forget it
        forgotten = column[:]
        amount = int(math.ceil(percent * len(column)))
        forget_this = []

        while len(forget_this) < amount:
            idx = random.randint(0, len(forgotten) - 1)
            if idx not in forget_this:
                forget_this.append(idx)

        for idx in forget_this:
            forgotten[idx] = missing_character

        return forgotten

    else:
        # if we want to forget > 50%, it is actually simpler
        # to forget everything and remember only (100-x)%
        percent = 1 - percent
        remembered = [missing_character for x in column]
        amount = int(math.ceil(percent * len(column)))
        remember_this = []

        while len(remember_this) < amount:
            idx = random.randint(0, len(remembered) - 1)
            if idx not in remember_this:
                remember_this.append(idx)

        for idx in remember_this:
            remembered[idx] = column[idx]

        return remembered


# parse and fetch the command-line arguments
args = parse_args()
data_file = args.data_file
attributes = args.attributes
if attributes is not None:
    attributes = attributes.split(",")
seed = args.seed
percent = args.percentage / 100.0
out_file = args.output_file
out_file_type = args.output_type
missing_character = args.missing_character

# set the seed for the RNG
random.seed(seed)

# fetch the header and data from the dataset file
arff_meta = []
(hdr, data_frame) = fetch_data(data_file)

# if the user did not specify any attributes to forget, we just
# apply the forgetting to all attributes
if attributes is None or len(attributes) <= 0:
    attributes = hdr

# do the forgetting
for attr in attributes:
    data_frame[attr] = forget(data_frame[attr], percent)

    # calculate how many entries we forgot (for debugging purposes)
    cnt = 0
    for x in data_frame[attr]:
        if x == missing_character:
            cnt += 1

# depending on whether an output file was specified, write it into that file
# or print it to stdout
lines = make_lines(hdr, data_frame, arff_meta)
if out_file is not None:
    with open(out_file, "w") as out:
        for line in lines:
            out.write(line + "\n")
else:
    for line in lines:
        try:
            print(line)
        except:
            sys.stderr.close()
