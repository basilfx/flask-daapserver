from daapserver.daap_data import dmapNames, dmapCodeTypes

import argparse
import astor
import ast
import sys


class DAAPObjectTransformer(ast.NodeTransformer):
    """
    Convert all DAAPObject(x, y) into SpeedyDAAPObject(code[x], type[x], y).
    """

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == "DAAPObject" \
                and len(node.args) == 2 and isinstance(node.args[0], ast.Str):
            code = dmapNames[node.args[0].s]
            itype = dmapCodeTypes[code][1]

            node.func.id = "SpeedyDAAPObject"
            node.args[0].s = code
            node.args.insert(1, ast.Num(itype))

        return self.generic_visit(node)


def parse_arguments():
    """
    Parse commandline arguments.
    """

    # Parse arguments and configure application instance.
    parser = argparse.ArgumentParser()

    # Add options
    parser.add_argument("input_file", type=str)
    parser.add_argument("output_file", type=str)

    # Parse command line
    return parser.parse_args(), parser


def parse_file(input_file, output_file):
    """
    Read `input_file' and produce an `output_file'.
    """

    # Read the file
    with open(input_file, "r") as fp:
        source = fp.read()

    # Convert function calls
    tree = ast.parse(source)
    new_tree = DAAPObjectTransformer().visit(tree)
    new_source = astor.to_source(new_tree)

    # Output new file
    with open(output_file, "w") as fp:
        fp.write(new_source)


def main():
    """
    Wrapper for command line access.
    """

    # Parse arguments and configure application instance.
    arguments, parser = parse_arguments()

    return parse_file(arguments.input_file, arguments.output_file)


# E.g. `python transform_daap_object.py'
if __name__ == "__main__":
    sys.exit(main())
