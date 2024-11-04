from pathlib import Path
import pandas as pd


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    concatenated = pd.concat([pd.read_csv(x, sep=";") for x in args.input])
    concatenated.to_csv(args.output, index=False, sep=";")
