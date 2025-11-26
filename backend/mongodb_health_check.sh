#!/bin/bash
# Script de surveillance MongoDB - détecte les arrêts et les logs

LOG_FILE="/var/log/mongodb_health.log"
CHECK_INTERVAL=30  # Vérification toutes les 30 secondes

while true; do
    if ! pgrep -x mongod > /dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ ALERTE: MongoDB n'est pas en cours d'exécution!" >> "$LOG_FILE"
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] Tentative de redémarrage via supervisorctl..." >> "$LOG_FILE"
        supervisorctl restart mongodb >> "$LOG_FILE" 2>&1
    else
        # MongoDB est en cours d'exécution - vérifier la connectivité
        if ! mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  MongoDB est lancé mais ne répond pas aux commandes" >> "$LOG_FILE"
        fi
    fi
    sleep "$CHECK_INTERVAL"
done
