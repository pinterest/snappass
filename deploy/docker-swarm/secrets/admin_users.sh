#!/bin/bash

declare -A USERS
USERS[admin]=SOME_PASSWORD

for K in "${!USERS[@]}"
do 
    echo $K:$(openssl passwd -apr1 "${USERS[$K]}")
done | paste -s -d, -