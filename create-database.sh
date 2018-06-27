#!/usr/bin/env bash

n=0
until [ ${n} -ge 3 ]
   do
    psql -v ON_ERROR_STOP=0 --username "postgres" --dbname "postgres" <<-EOSQL && break
        CREATE USER trillian WITH PASSWORD '${PGPASSWORD}';
        ALTER USER trillian WITH PASSWORD '${PGPASSWORD}';
        CREATE DATABASE trillian WITH OWNER trillian TEMPLATE template_postgis;
EOSQL

    echo "Retrying in 5" >&2
    n=$[$n+1]
    sleep 5
done
