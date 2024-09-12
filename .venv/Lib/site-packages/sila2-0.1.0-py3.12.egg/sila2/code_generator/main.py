import os
import sys
from argparse import ArgumentParser
from typing import List, Optional

import sila2.code_generator
from sila2.code_generator.package_generator import PackageGenerator
from sila2.framework import Feature


def main(argv: Optional[List[str]] = None):
    parser = ArgumentParser(
        prog=sila2.code_generator.__name__,
        description="Generate Python package for a SiLA 2 server application from given feature definitions",
    )
    parser.add_argument("-p", "--package", help="Generate full package with given name", required=False)
    parser.add_argument("-o", "--out-dir", help="Output directory (default: '.')", default=".")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Override existing files (always true for feature-specific auto-generated files)",
    )
    parser.add_argument("--debug", action="store_true", help="Display more detailed error messages")
    parser.add_argument("feature_definitions", nargs="*", help="SiLA 2 feature definitions")

    args = parser.parse_args(argv)

    try:
        os.makedirs(args.out_dir, exist_ok=True)
        features = [
            Feature(open(feature_definition_file).read()) for feature_definition_file in args.feature_definitions
        ]
        PackageGenerator(args.out_dir, args.package, features, overwrite=args.overwrite).generate()
    except Exception as ex:
        if args.debug:
            raise ex

        print(f"{ex.__class__.__name__}: {ex}", file=sys.stderr)
        exit(1)
