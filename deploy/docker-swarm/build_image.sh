#!/bin/bash

VERSION="1.6.0"
RELEASE="https://github.com/pinterest/snappass/archive/refs/tags/v$VERSION.tar.gz"
DOCKER_REPOSITORY="<your-repo>/snappass"
DOCKER_TAG="$VERSION"

set -e -u -x -o pipefail

rm -rf "snappass-$VERSION"

curl -L "$RELEASE" -o - | tar -zxf -

cd "snappass-$VERSION"

docker build -f Dockerfile -t $DOCKER_REPOSITORY:$VERSION .
docker push $DOCKER_REPOSITORY:$VERSION