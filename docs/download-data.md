# Downloading the data

The data record is hosted in a Zenodo-repository at
<https://zenodo.org/uploads/14266867>. Information regarding the organization of
the data may be found in the repository, and the data may be downloaded from
there.

Alternatively, we provide a python script relying on the Zenodo REST API, to
download the full data records, or individual zipped archives. The script is
located in `scripts/zenodo_download.py`, requires only a default python
installation, and may be run with:

```bash
# List all available files in the repo
python3 scripts/zenodo_download.py --list

# Download  all files into the directory 'outputdir'
python3 scripts/zenodo_download.py --all  --output outputdir

# Download only the file "README.md" into the current directory
python3 scripts/zenodo_download.py --filename README.md --output .
```
