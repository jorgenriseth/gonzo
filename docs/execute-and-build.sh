#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_ROOT="${GONZO_DATA_ROOT:-$ROOT}"
BUILD_ROOT="$ROOT/_build/documentation"
TIMEOUT=1200
PREPARE_ONLY=false

while [[ $# -gt 0 ]]; do
	case "$1" in
		--data-root) DATA_ROOT="${2:?Missing --data-root value}"; shift 2 ;;
		--build-root) BUILD_ROOT="${2:?Missing --build-root value}"; shift 2 ;;
		--timeout) TIMEOUT="${2:?Missing --timeout value}"; shift 2 ;;
		--prepare-only) PREPARE_ONLY=true; shift ;;
		-h|--help)
			echo "Usage: $0 [--data-root PATH] [--build-root PATH] [--timeout SECONDS] [--prepare-only]"
			exit 0 ;;
		*) echo "Unknown option: $1" >&2; exit 1 ;;
	esac
done

DATA_ROOT="$(realpath -e "$DATA_ROOT")"
BUILD_ROOT="$(realpath -m "$BUILD_ROOT")"
case "$BUILD_ROOT/" in
	"$ROOT/"|"$DATA_ROOT/"|"$ROOT/docs/"*|"$DATA_ROOT/mri_dataset/"*|"$DATA_ROOT/mri_processed_data/"*)
		echo "Build directory must be separate from source docs and data directories" >&2
		exit 1 ;;
esac
[[ "$TIMEOUT" =~ ^[1-9][0-9]*$ ]] || { echo "Timeout must be a positive integer" >&2; exit 1; }
for tree in mri_dataset mri_processed_data; do
	[[ -d "$DATA_ROOT/$tree" ]] || { echo "Missing data tree: $DATA_ROOT/$tree" >&2; exit 1; }
	if [[ -e "$BUILD_ROOT/$tree" && ! -L "$BUILD_ROOT/$tree" ]]; then
		echo "Refusing to replace existing data directory: $BUILD_ROOT/$tree" >&2
		exit 1
	fi
done

mkdir -p "$BUILD_ROOT/docs" "$BUILD_ROOT/figures"
cp -a "$ROOT/docs/." "$BUILD_ROOT/docs/"
cp "$ROOT/myst.yml" "$BUILD_ROOT/myst.yml"
for tree in mri_dataset mri_processed_data; do
	ln -sfnT "$DATA_ROOT/$tree" "$BUILD_ROOT/$tree"
done

python - "$ROOT/myst.yml" > "$BUILD_ROOT/notebooks.txt" <<'PY'
from pathlib import Path
import sys
import yaml

def toc_files(entries):
	for entry in entries:
		if "file" in entry:
			yield entry["file"]
		yield from toc_files(entry.get("children", []))

config = yaml.safe_load(Path(sys.argv[1]).read_text())
for path in dict.fromkeys(toc_files(config["project"]["toc"])):
	if Path(path).suffix == ".ipynb":
		print(path)
PY

printf 'Data root: %s\nBook workspace: %s\n' "$DATA_ROOT" "$BUILD_ROOT"
cd "$BUILD_ROOT"
while IFS= read -r notebook; do
	jupyter nbconvert --to notebook --inplace --ClearOutputPreprocessor.enabled=True "$notebook"
	if [[ "$PREPARE_ONLY" == false ]]; then
		echo "Executing: $notebook"
		MPLBACKEND=module://matplotlib_inline.backend_inline \
			jupyter nbconvert --to notebook --execute --inplace \
				--ExecutePreprocessor.timeout="$TIMEOUT" \
				--ExecutePreprocessor.kernel_name=python3 "$notebook"
	fi
done < "$BUILD_ROOT/notebooks.txt"

if [[ "$PREPARE_ONLY" == false ]]; then
	jupyter-book build --html --ci
	echo "HTML build completed under $BUILD_ROOT/_build/html"
fi
