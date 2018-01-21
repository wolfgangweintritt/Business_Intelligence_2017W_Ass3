#!/usr/bin/env python
"""Take a dataset and replace hidden values with the mean or median of other values."""

import argparse
import sys


def output_type(arg):
    """Check if we support the output type supported (CSV or ARFF)"""
    arg = str(arg).lower()
    if arg not in ["csv", "arff"]:
        raise argparse.ArgumentTypeError("Only CSV and ARFF are supported")

    return arg

def parse_args():
    """Parse the command-line arguments for the script"""

    description = "Replace missing values from the dataset with the median or mean of other values."
    
    epilog = "Thanks for using the replace service!"

    parser = argparse.ArgumentParser(description=description,
                                     epilog=epilog)

    parser.add_argument("value_type",
                        metavar="VALUE_TYPE",
                        type=str,
                        help="The replacement type for the missing values, either 'mean' or 'median'",
                        choices=["mean", "median"],
                        default="mean")
                        
    parser.add_argument("value_source",
                        metavar="SOURCE",
                        type=str,
                        help="The source from where replacement values will be calculated, either 'all' or 'class'",
                        choices=["all", "class"],
                        default="all")

    parser.add_argument("-c", "--missing-character",
                        metavar="CHAR",
                        type=str,
                        help="Character (or string) used to mark a missing entry",
                        default="?")

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


def replace(column, type, source, classes):
    """Replace missing values in the column"""
    replacementValue = 0.0
    classReplacement = [0.0] * 4
    mean = 0.0
    count = 0
    median = []
    classMean = [0.0] * 4
    classCount = [0] * 4
    classMedian = [[]] * 4
    for i, value in enumerate(column):
        if value != missing_character:
            value = float(value)
            count += 1
            mean += value
            median.append(value)
            classCount[int(classes[i]) - 1] += 1
            classMean[int(classes[i]) - 1] += value
            classMedian[int(classes[i]) - 1].append(value)

    if source == "all":
        if type == "mean":
            mean = mean / count
            replacementValue = mean
            
        else:
            median.sort()
            if len(median) % 2 == 1:
                replacementValue = median[int((len(median) - 1) / 2)]
            else:
                replacementValue = median[int((len(median) / 2) - 1)]

        for i, value in enumerate(column):
            if value == missing_character:
                column[i] = "{:.3f}".format(replacementValue)
                
    else:
        if type == "mean":
            for i, mean in enumerate(classMean):
                classMean[i] = mean / classCount[i]
                classReplacement[i] = classMean[i]

        else:
            for i, c in enumerate(classMedian):
                classMedian[i].sort()
                if len(classMedian[i]) % 2 == 1:
                    classReplacement[i] = classMedian[i][int((len(classMedian[i]) - 1) / 2)]
                else:
                    classReplacement[i] = classMedian[i][int((len(classMedian[i]) / 2) - 1)]

        for i, value in enumerate(column):
            if value == missing_character:
                column[i] = "{:.3f}".format(classReplacement[int(classes[i]) - 1])


    return column


# parse and fetch the command-line arguments
args = parse_args()
type = args.value_type
source = args.value_source
data_file = args.data_file
out_file = args.output_file
out_file_type = args.output_type
missing_character = args.missing_character

# fetch the header and data from the dataset file
arff_meta = []
(hdr, data_frame) = fetch_data(data_file)

# do the replacing
for attr in hdr:
    missingCheck = False
    for value in data_frame[attr]:
        if value == missing_character:
            missingCheck = True
    if missingCheck == True:
        data_frame[attr] = replace(data_frame[attr], type, source, data_frame["Class"])

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
