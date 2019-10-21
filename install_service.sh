#!/bin/sh

if [ "$(id -u)" != "0" ]; then
  echo "Run this as root."
  exit 1
fi

SERVICE_TO_INSTALL=${1?"Please enter a service file to install."}
SYSTEM_DIR=/lib/systemd/system/

cp $SERVICE_TO_INSTALL $SYSTEM_DIR$SERVICE_TO_INSTALL
echo "Copied $SERVICE_TO_INSTALL into $SYSTEM_DIR."

chmod 644 $SYSTEM_DIR$SERVICE_TO_INSTALL
echo "Set permissions."

echo "Reloading services..."
systemctl daemon-reload

echo "Done."
