"""
CLI for Hedgehog prediction given an input FASTA file.
"""
import os

from argparse import ArgumentParser
import yaml

from selene_sdk.utils import load_path
from selene_sdk.utils import parse_configs_and_run


def _finditem(obj, val):
    for k, v in obj.items():
        if hasattr(v, 'keywords'):
            _finditem(v.keywords, val)
        elif isinstance(v, dict):
            _finditem(v, val)
        elif isinstance(v, str) and '<PATH>' in v:
            obj[k] = v.replace('<PATH>', val)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "--yaml",
        required=True,
        help="Input YAML configuration file path"
    )
    parser.add_argument(
        "--fasta",
        required=True,
        help="Input FASTA file to process"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory to store output files"
    )
    parser.add_argument(
        "--cuda",
        action="store_true",
        help="Use CUDA for processing"
    )
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Assumes that the `models` directory is in the same directory as this
    # script. Please update this line if not.
    use_dir = os.path.dirname(os.path.abspath(__file__))
    use_cuda = args.cuda

    configs = load_path(args.yaml, instantiate=False)
    fp = configs["analyze_sequences"].keywords["trained_model_path"]
    _finditem(configs, use_dir)

    configs["prediction"]["input_path"] = args.fasta
    configs["prediction"]["output_dir"] = args.output_dir
    parse_configs_and_run(configs)
