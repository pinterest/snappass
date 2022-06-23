#!/bin/bash

export DOMAIN="some.domain.com"
export USERS=$(bash secrets/admin_users.sh)
export SECRET_KEY="SOME_SECRET_KEY"
export IMAGE="pinterest/snappass:1.6.0"