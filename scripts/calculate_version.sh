#!/usr/bin/env bash
VERSION=$(python setup.py --version)


if [ -z $VERSION ]; then
      echo "The base version is not set."
      exit 1
fi

if [ $BRANCH == 'stable' ]; then
    echo $VERSION
    exit 1
fi

git fetch --tags

for (( NUMBER=0; ; NUMBER++ ))
do
    FULL_VERSION="$VERSION-$BRANCH.$NUMBER"
    if ! [ $(git tag -l ?$FULL_VERSION) ]; then
        echo $FULL_VERSION
        break
    fi
done