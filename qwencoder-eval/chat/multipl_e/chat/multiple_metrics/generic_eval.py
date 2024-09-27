# This is a helper script for evaluating benchmarks that have been translated to
# different languages.
#
# To use this script, call eval_lang.py.
# The --directory argument is required, and tells the script where the benchmarks are located.
# The --files argument is optional, and takes a list of numbers corresponding to the files to be evaluated.
#
# The script will print the results on each benchmark, and also write to results/lang.csv.
# When the script completes, it will print a summary.
#
# Examples
#
# To run the entire benchmark suite:
#   python3 src/eval_php.py --directory datasets/php-keep-code_davinci_001_temp_0.2-0/
#
# To run benchmarks 1, 2, and 3:
#   python3 src/eval_php.py --directory datasets/php-keep-code_davinci_001_temp_0.2-0/ --files 1 2 3

import argparse
import sys
from pathlib import Path
from sys import exit as sysexit


def list_files(directory, ext):
    files_unsorted = directory.glob(f"HumanEval_*{ext}")
    # assumption: base filenames are in the format of HumanEval_X_*
    # Where X is a valid number
    def key(s):
        return int(str(s.name).split("_")[1])

    files_sorted = sorted(files_unsorted, key=(lambda s: key(s)))

    # assumption: there may be missing files, but no extra files
    # so we build files_array where the index corresponds to the file's number,
    # and a missing file is represented by None
    size = key(files_sorted[-1]) + 1
    files_array = [None] * size
    for f in files_sorted:
        k = key(f)
        files_array[k] = f

    return files_array


def main(eval_script, language, extension):
    args = argparse.ArgumentParser()

    args.add_argument(
        "--directory", type=str, required=True, help="Directory to read benchmarks from"
    )
    args.add_argument(
        "--files",
        type=int,
        nargs="*",
        default=[],
        help="Specify the benchmarks to evaluate by their number, e.g. --files 0 1 2",
    )
    args = args.parse_args()

    directory = Path(args.directory).resolve()

    files_sorted = list_files(directory, extension)

    # the directory you specified does not contain the right language
    if len(files_sorted) == 0:
        print(f"The specified directory does not contain files of type {extension}")
        sysexit(1)

    files_index = []
    if len(args.files) > 0:
        files_index = args.files
    else:
        files_index = range(len(files_sorted))

    total = 0
    passed = 0
    syntax_error = 0

    results_file = Path(
        Path(__file__).parent, "..", "results", language.lower() + ".csv"
    ).resolve()

    with open(results_file, "w") as f:
        for i in files_index:
            filepath = files_sorted[i]
            if filepath is None:
                print("File {} does not exist!".format(i))
                continue
            res = eval_script(filepath)
            output = f"{language},{filepath.stem},{res['status']}\n"
            f.write(output)
            print(output, end="")
            total += 1
            if res["status"] == "OK":
                passed += 1
            elif res["status"] == "SyntaxError":
                syntax_error += 1
    print(f"Total {total}, Syntax Error {syntax_error}, Passed {passed}")


def main_check_stubs(check_script, language, extension):
    args = argparse.ArgumentParser()

    args.add_argument(
        "--directory", type=str, required=True, help="Directory to read benchmarks from"
    )
    args.add_argument(
        "--files",
        type=int,
        nargs="*",
        default=[],
        help="Specify the benchmarks to evaluate by their number, e.g. --files 0 1 2",
    )
    args = args.parse_args()

    directory = Path(args.directory).resolve()

    files_sorted = list_files(directory, extension)

    # the directory you specified does not contain the right language
    if len(files_sorted) == 0:
        print(f"The specified directory does not contain files of type {extension}")
        sysexit(1)

    files_index = []
    if len(args.files) > 0:
        files_index = args.files
    else:
        files_index = range(len(files_sorted))

    total = 0
    passed = 0

    results_file = Path(
        Path(__file__).parent, "..", "check_results", language.lower() + ".csv"
    ).resolve()

    with open(results_file, "w") as f:
        for i in files_index:
            filepath = files_sorted[i]
            if filepath is None:
                print("File {} does not exist!".format(i))
                continue
            res = check_script(filepath)
            output = f"{language},{filepath.stem},{res['status']}\n"
            f.write(output)
            print(output, end="")
            total += 1
            if res["status"] == "OK":
                passed += 1
    print(f"Total {total}, Passed {passed}")

    if total != passed:
        sys.exit(1)
