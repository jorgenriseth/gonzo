#!/bin/bash
# Execute all notebooks in the docs directory, then build the book

DOCS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DOCS_DIR"

# List of notebooks to skip during execution
SKIP_NOTEBOOKS=(
    "gonzo-dicom-extraction.ipynb"
)

echo "======================================"
echo "Executing Jupyter Notebooks in docs/"
echo "======================================"
echo ""

# Find all .ipynb files (excluding hidden and build directories)
notebooks=$(find . -name "*.ipynb" -not -path "./_build/*" -not -path "./.*" | sort)

if [ -z "$notebooks" ]; then
    echo "No notebooks found to execute."
else
    for notebook in $notebooks; do
        # Extract just the filename
        notebook_name=$(basename "$notebook")
        
        # Check if notebook should be skipped
        skip=false
        for skip_nb in "${SKIP_NOTEBOOKS[@]}"; do
            if [ "$notebook_name" = "$skip_nb" ]; then
                skip=true
                break
            fi
        done
        
        if [ "$skip" = true ]; then
            echo "⏭️  Skipping: $notebook"
        else
            echo "Executing: $notebook"
            jupyter nbconvert --to notebook --execute --inplace "$notebook" || {
                echo "⚠️  Warning: Failed to execute $notebook"
                # Continue with other notebooks even if one fails
            }
        fi
        echo ""
    done
fi

echo ""
echo "======================================"
echo "Building Jupyter Book"
echo "======================================"
echo ""

# Stay in docs directory for building
jupyter-book build --all .

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Done! Book built at docs/_build/html/index.html"
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi
