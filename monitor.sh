#!/bin/bash

export PGPASSWORD='lab123'

CPU_LOAD=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
RAM_FREE_MB=$(free -m | awk '/^Mem/ {print $4}')
DISK_FREE_GB=$(df -BG / | awk 'NR==2 {print $4}' | tr -d 'G')

if systemctl is-active --quiet nginx; then
    NGINX_STATUS="active"
else
    NGINX_STATUS="inactive"
fi

if systemctl is-active --quiet postgresql; then
    POSTGRES_STATUS="active"
else
    POSTGRES_STATUS="inactive"
fi

psql -U cloud_user -d cloud_lab -h localhost -c \
"INSERT INTO metrics (timestamp, cpu_load, ram_free_mb, disk_free_gb, nginx_status, postgres_status) \
VALUES (NOW(), $CPU_LOAD, $RAM_FREE_MB, $DISK_FREE_GB, '$NGINX_STATUS', '$POSTGRES_STATUS');"

echo "$(date): CPU=$CPU_LOAD%, RAM=$RAM_FREE_MB MB, DISK=$DISK_FREE_GB GB, nginx=$NGINX_STATUS, postgres=$POSTGRES_STATUS" >> /home/csn/monitor.log
