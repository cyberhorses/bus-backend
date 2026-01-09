#!/bin/sh

set -e
DB_NAME="bus_app"
DB_USER="root"
SCHEMA_FILE=tables.sql

#sudo systemctl start mariadb
#sudo systemctl enable mariadb

echo "> mariadb started"

sudo mariadb <<EOF
CREATE DATABASE IF NOT EXISTS ${DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '${DB_USER}'@'localhost' IDENTIFIED BY '${DB_PASS}';
GRANT ALL PRIVILEGES ON ${DB_NAME}.* TO '${DB_USER}'@'localhost';
FLUSH PRIVILEGES;
EOF

mariadb -u${DB_USER} ${DB_NAME} < "$SCHEMA_FILE"

echo "> Setup complete"
