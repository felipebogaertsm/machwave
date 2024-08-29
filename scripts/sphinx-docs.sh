#!/bin/bash

SPHINXBUILD="sphinx-build"
SPHINXAPIDOC="sphinx-apidoc"
SPHINXQUICK="sphinx-quickstart"
SOURCEDIR="docs"
OUTPUTDIR="docs/_build/html"
PROJECTDIR="machwave"
PROJECT_NAME="Machwave"
AUTHOR_NAME="Felipe Bogaerts de Mattos"
RELEASE="0.1.0"
LANGUAGE="en"

quickstart() {
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
}

apidoc() {
    echo "Running sphinx-apidoc..."
    $SPHINXAPIDOC -o $SOURCEDIR $PROJECTDIR
    echo "sphinx-apidoc completed."
}

html() {
    echo "Building HTML documentation..."
    $SPHINXBUILD -M html $SOURCEDIR $OUTPUTDIR
    echo "HTML documentation built in $OUTPUTDIR."
}

"$1"