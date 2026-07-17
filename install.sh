#!/bin/bash
# ============================================================
#  LVM Panel Pro - Complete Installer (PEP 668 compliant)
#  Repo: https://github.com/Vmallu00/Panal-vps
# ============================================================

set -e  # Exit on any error

# --------------------------------------------
# 1. ROOT CHECK
# --------------------------------------------
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root: sudo bash install.sh"
    exit 1
fi

# --------------------------------------------
# 2. SYSTEM UPDATE & DEPENDENCIES
# --------------------------------------------
echo "============================================="
echo "  LVM Panel Pro - Multi-Node VPS Panel"
echo "  Installing system dependencies..."
echo "============================================="

apt update && apt upgrade -y
apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-full \
    git \
    docker.io \
    docker-compose \
    curl \
    wget \
    nginx \
    openssl

# Start Docker
systemctl enable docker
systemctl start docker

# --------------------------------------------
# 3. CREATE INSTALL DIRECTORY
# --------------------------------------------
INSTALL_DIR="/opt/lvm-panel-pro"
echo "📁 Installing panel to: $INSTALL_DIR"

# Remove old install if present
if [ -d "$INSTALL_DIR" ]; then
    echo "⚠️  Old installation detected. Removing..."
    rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"

# Copy all files from the repo (where install.sh is located)
# If running via curl pipe, the files aren't copied. We need to clone the repo.
if [ -d ".git" ] || [ -f "app.py" ]; then
    # We are inside the repo folder
    cp -r . "$INSTALL_DIR/"
else
    # We are running from a curl pipe, clone the repo
    echo "📦 Cloning repository into $INSTALL_DIR..."
    git clone https://github.com/Vmallu00/Panal-vps.git "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# --------------------------------------------
# 4. CREATE PYTHON VIRTUAL ENVIRONMENT
# --------------------------------------------
echo "🐍 Creating Python virtual environment (fixes PEP 668)..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip inside venv
venv/bin/pip install --upgrade pip

# Install Python packages inside the venv
echo "📦 Installing Python packages..."
venv/bin/pip install flask flask-login requests docker psutil gunicorn

# --------------------------------------------
# 5. GENERATE SECRET KEY
# --------------------------------------------
SECRET=$(openssl rand -hex 32)
sed -i "s/CHANGE_ME/$SECRET/g" app.py

# --------------------------------------------
# 6. INITIALIZE DATABASE (First run)
# --------------------------------------------
echo "🗄️  Initializing database..."
venv/bin/python -c "from app import app, init_db; app.app_context().push(); init_db()"

# --------------------------------------------
# 7. CREATE SYSTEMD SERVICE (using venv)
# --------------------------------------------
cat > /etc/systemd/system/lvm-panel.service <<EOF
[Unit]
Description=LVM Panel Pro (Multi-Node VPS Management)
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and start the service
systemctl daemon-reload
systemctl enable lvm-panel
systemctl restart lvm-panel

# --------------------------------------------
# 8. OPTIONAL: INSTALL NODE AGENT ON THIS SAME SERVER
# --------------------------------------------
echo ""
read -p "❓ Do you also want to run the Node Agent on this server? (y/n): " install_agent

if [[ "$install_agent" =~ ^[Yy]$ ]]; then
    echo "🚀 Installing Node Agent on this server..."

    # Create agent directory
    mkdir -p /opt/node-agent
    cp node_agent.py /opt/node-agent/

    # Generate random API key for the agent
    AGENT_KEY=$(openssl rand -hex 32)

    # Install agent dependencies in a separate venv (or system-wide with --break)
    python3 -m venv /opt/node-agent/venv
    /opt/node-agent/venv/bin/pip install flask docker psutil

    # Create systemd service for the agent
    cat > /etc/systemd/system/node-agent.service <<EOF
[Unit]
Description=LVM Node Agent
After=docker.service network.target
Requires=docker.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/node-agent
Environment="NODE_API_KEY=$AGENT_KEY"
Environment="AGENT_PORT=9000"
ExecStart=/opt/node-agent/venv/bin/python /opt/node-agent/node_agent.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable node-agent
    systemctl start node-agent

    echo ""
    echo "✅ Node Agent installed!"
    echo "   API Key: $AGENT_KEY"
    echo "   URL: http://$(curl -s ifconfig.me):9000"
    echo ""
    echo "👉 Add this node in the panel: Admin → Nodes → Add Node"
fi

# --------------------------------------------
# 9. GET SERVER IP
# --------------------------------------------
SERVER_IP=$(curl -s ifconfig.me || echo "localhost")

# --------------------------------------------
# 10. DONE!
# --------------------------------------------
echo ""
echo "============================================================"
echo "  ✅ INSTALLATION COMPLETE!"
echo "============================================================"
echo ""
echo "  🌐 Panel URL:      http://$SERVER_IP:5000"
echo "  👤 Username:       admin"
echo "  🔑 Password:       admin123"
echo ""
echo "  📁 Panel location: $INSTALL_DIR"
echo "  📊 Status:         systemctl status lvm-panel"
echo "  📜 Logs:           journalctl -u lvm-panel -f"
echo ""
if [[ "$install_agent" =~ ^[Yy]$ ]]; then
    echo "  🤖 Agent Status:   systemctl status node-agent"
    echo "  🔑 Agent API Key:  $AGENT_KEY"
    echo "  🔗 Agent URL:      http://$SERVER_IP:9000"
fi
echo ""
echo "  ⚠️  CHANGE THE DEFAULT PASSWORD IMMEDIATELY!"
echo "============================================================"
