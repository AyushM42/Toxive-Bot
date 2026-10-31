#!/bin/sh
# Installs and starts the bot and squirrel display as services. Run from the bot folder:
#   sh deploy/install.sh
set -e
DIR=$(pwd)
USER_NAME=$(whoami)
for name in toxive-bot toxive-squirrel; do
    sed -e "s|__DIR__|$DIR|g" -e "s|__USER__|$USER_NAME|g" "deploy/$name.service" | sudo tee "/etc/systemd/system/$name.service" > /dev/null
done
sudo systemctl daemon-reload
sudo systemctl enable --now toxive-bot toxive-squirrel
echo "Installed. Logs: journalctl -u toxive-bot -f   /   journalctl -u toxive-squirrel -f"
