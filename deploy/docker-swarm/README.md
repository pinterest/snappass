# How to deploy

This assumes you have a Docker swarm running. Once set up, you will need a
traefik instance configured to work with constraint `traefik-public` and a network `traefik-public`.

This also expects encryption to be handled outside of docker swarm by a LB that has access to the Swarm.

## 1. Adapt passwords for admin users

Admin users are users that are allowed to create new passwords.
To manage these users, simply adapt the file `secrets/admin_users.sh`

## 2. Adapt values in vars.sh

`vars.sh` includes settings for the domain as well as the secret key that is used for Flask. Adapt them accordingly.

## 3. Run deploy

```
bash deploy.sh
```

## 4. Use it

You can now find your snappass application under:

`https://some.domain.com`

Creating new passwords will require a valid login from `admin_users.sh`.

Accessing them does not require a password.
