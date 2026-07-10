#!/bin/bash

set -a

source ./vars.sh

docker stack deploy --with-registry-auth -c snappass.yml snappass
