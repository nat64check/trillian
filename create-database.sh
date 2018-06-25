#!/usr/bin/env bash
set -e

psql -v ON_ERROR_STOP=0 --username "postgres" --dbname "postgres" <<-EOSQL
    CREATE USER trillian WITH PASSWORD '${PGPASSWORD}';
    ALTER USER trillian WITH PASSWORD '${PGPASSWORD}';
    CREATE DATABASE trillian WITH OWNER trillian TEMPLATE template_postgis;
EOSQL
