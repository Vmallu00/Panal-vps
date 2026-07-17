#!/bin/bash
set -e
echo "========================================="
echo "  LVM Panel Pro – Multi‑Node Installer"
echo "========================================="

apt update && apt upgrade -y
apt install -y python3 python3-pip git docker.io docker-compose curl wget nginx

pip3 install --upgrade pip
pip3 install -r requirements.txt

mkdir -p /opt/lvm-panel-pro
cp -r . /opt/lvm-panel-pro/
cd /opt/lvm-panel-pro

# Generate a random secret key
SECRET=$(openssl rand -hex 32)
sed -i "s/CHANGE_ME/$SECRET/g" app.py

# Panel service
cat > /etc/systemd/system/lvm-panel.service <<EOF
[Unit]
Description=LVM Panel Pro
After=network.target docker.service
[Service]
Type=simple
User=root
WorkingDirectory=/opt/lvm-panel-pro
ExecStart=/usr/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=10
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable lvm-panel
systemctl start lvm-panel

echo "========================================="
echo "✅ Panel installed!"
echo "👉 http://$(curl -s ifconfig.me):5000"
echo "Default login: admin / admin123"
echo "========================================="
