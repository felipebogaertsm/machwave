#!/bin/bash

SPHINXBUILD="sphinx-build"
SPHINXQUICK="sphinx-quickstart"
SOURCEDIR="machwave/docs"
OUTPUTDIR="machwave/docs/_build/html"
PROJECT_NAME="Machwave"
AUTHOR_NAME="Felipe Bogaerts de Mattos"
RELEASE="0.1.0"
LANGUAGE="en"

echo "Checking if $SOURCEDIR exhists..."
if [ ! -d "$SOURCEDIR" ]; then
    echo "WARNING: $SOURCEDIR not found. Creating directory..."
    mkdir -p $SOURCEDIR
    echo "$SOURCEDIR created."
fi

echo "Running sphinx-quickstart..."
$SPHINXQUICK $SOURCEDIR \
    --quiet \
    --project="$PROJECT_NAME" \
    --author="$AUTHOR_NAME" \
    --release="$RELEASE" \
    --language="$LANGUAGE" \
    --extensions=sphinx.ext.autodoc,sphinx.ext.viewcode,sphinx.ext.napoleon
echo "sphinx-quickstart completed."

# Check if conf.py was created
if [ ! -f "$SOURCEDIR/conf.py" ]; then
    echo "ERROR: conf.py not found in $SOURCEDIR. sphinx-quickstart may have failed."
    exit 1
fi

echo "Building HTML documentation..."
$SPHINXBUILD -M html $SOURCEDIR $OUTPUTDIR
echo "HTML documentation built in $OUTPUTDIR."
