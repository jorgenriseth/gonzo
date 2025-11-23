import argparse
import dataclasses
import json
from urllib import request


@dataclasses.dataclass
class Settings:
    api_url: str = "https://zenodo.org/api/deposit/depositions/14266867"


def get_file_list(settings: Settings) -> list[dict[str, str]]:
    url = f"{settings.api_url}/files"
    
    with request.urlopen(url) as response:
        return json.loads(response.read().decode())


def find_file_id(filename: str, files: list[dict[str, str]], settings: Settings) -> str:
    file_ids = [
        deposition_file["id"]
        for deposition_file in files
        if deposition_file["filename"] == filename
    ]
    if len(file_ids) == 0:
        raise ValueError(f"Couldn't find {filename} in deposition")
    if len(file_ids) > 1:  # Not sure if this can happen.
        raise ValueError(f"Multiple files found named {filename}.")
    return file_ids[0]


def download_single_file(file_download_url: str, output: str, settings: Settings):
    with request.urlopen(file_download_url) as response:
        with open(output, "wb") as f:
            f.write(response.read())


def list_all_files(files: list[dict[str, str]]):
    for deposition_file in files:
        print(deposition_file["filename"])


def validate_input(parser):
    args = parser.parse_args()
    if args.ls:
        return args
    elif not args.output:
        raise parser.error("Missing required option '--output'.")
    if (not args.all) and (args.filename is None):
        parser.error("'--filename' option required without '--list' or '--all'")
    return args


def main():
    parser = argparse.ArgumentParser(description="Download files.")
    parser.add_argument(
        "--output",
        type=str,
        help="Output directory.",
    )
    parser.add_argument(
        "--filename",
        type=str,
        help="Name of file to download. Ignored if '--all' is used",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Download all available files.",
    )
    parser.add_argument(
        "--list",
        dest="ls",
        action="store_true",
        help="List files in record, without downloading.",
    )
    args = validate_input(parser)

    settings = Settings()
    files = get_file_list(settings)
    if args.ls:
        list_all_files(files)
        return

    if not args.all:
        if args.filename is None:
            parser.error("'--filename' option required without '--list' or '--all'")
        files = [file for file in files if file["filename"] == args.filename]
        if len(files) == 0:
            raise ValueError(f"Couldn't find {args.filename} in deposition")

    for file in files:
        print(f"Downloading file {file['filename']}")
        download_single_file(
            file["links"]["download"], f"{args.output}/{file['filename']}", settings
        )


if __name__ == "__main__":
    main()
