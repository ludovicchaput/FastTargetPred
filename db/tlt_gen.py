import sys
from pathlib import Path
from csv import DictReader


def generate__tlt_file(input, output):
    """
    Associate targets of the same molecule in one row from input file and output it in output file.
    Output file will be overwritten.
    :param input: file path
    :type input: str
    :param output: output file path
    :type output: str
    :return: None
    :rtype: None
    """
    input, output = Path(input), Path(output)

    assert input.is_file() is True

    input_file = input.open("r")

    table_dict = {}

    dr = DictReader(input_file, delimiter=" ", fieldnames=["molid", "tid"])
    for row in dr:
        molid = row["molid"]
        if molid not in table_dict:
            table_dict[molid] = set()
        table_dict[molid].add(row["tid"])

    input_file.close()

    output_file = output.open('w')
    for k, v in table_dict.items():
        output_file.write("{} {}\n".format(k, "  ".join(v)))
    output_file.close()


if __name__ == "__main__":
    try:
        assert len(sys.argv) == 3
        generate__tlt_file(sys.argv[1], sys.argv[2])
    except AssertionError:
        print("Usage : tlt_gen.py input output.")
        sys.exit(1)
