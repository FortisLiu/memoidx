import argparse


def main():
    parser = argparse.ArgumentParser(
        prog="memoidx",
        description="Local memory for coding agents",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="memoidx 0.1.0",
    )
    parser.parse_args()
    return 0
