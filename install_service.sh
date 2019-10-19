#!/bin/sh

if [ "$(id -u)" != "0" ]; then
  echo "Run this as root."
  exit 1
fi

SERVICE_TO_INSTALL=${1?"Please enter a service file to install."}

if [ ! -e /lib/systemd/system/$SERVICE_TO_INSTALL ]; then
  cp $SERVICE_TO_INSTALL /lib/systemd/system/$SERVICE_TO_INSTALL
fi

chmod 644 /lib/systemd/system/$SERVICE_TO_INSTALL
systemctl daemon-reload
