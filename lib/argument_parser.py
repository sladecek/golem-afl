"""Argument parser."""
import argparse

def build_parser(description: str):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--driver", help="Payment driver name, for example `zksync`")
    parser.add_argument("--network", help="Network name, for example `rinkeby`")
    parser.add_argument("--subnet-tag", default="community.3", help="Subnet name; default: %(default)s")
    parser.add_argument("--log-file", default=None, help="Log file for YAPAPI; default: %(default)s")
    parser.add_argument("--run-time", default=5, type=int, help="Runtime in minutes; default: %(default)d")
    parser.add_argument("--nodes", default=2, type=int, help="Number of nodes; default: %(default)d")
    parser.add_argument("--cycle", default=3, type=int, help="Number of repetitions; default: %(default)d")
    parser.add_argument("--prj", default='default', help="Project sub directory (in demo folder); default: %(default)d")
    return parser
