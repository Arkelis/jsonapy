#!/usr/bin/env sh

echo Removing current docs folder...
rm -rf docs
echo Building new docs...
poetry run pdoc \
    -e jsonapy=https://github.com/Arkelis/jsonapy/tree/master/jsonapy/ \
    -t scripts/docs \
    -o docs jsonapy
echo Adding .nojekyll file...
touch docs/.nojekyll
echo Adding CNAME file...
echo jsonapy.pycolore.fr > docs/CNAME
echo Done.
