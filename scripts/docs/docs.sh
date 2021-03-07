#!/usr/bin/env sh

if [[ `git status --porcelain` ]]; then
  echo  "Working directory must be clean"
  exit 1
fi
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
echo Switching to gh-pages branch...
git add docs
git stash
git checkout gh-pages
git stash pop --quiet
git checkout --theirs .
git add docs
git stash drop
echo Ready to commit.
