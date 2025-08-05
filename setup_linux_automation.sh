#!/bin/bash

# Linux Office Hours Server Automation Setup
# This script sets up automatic startup and shutdown using systemd

set -e

echo "Setting up Office Hours Server Automation for Linux..."

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Project directory: $SCRIPT_DIR"

# Make scripts executable
echo "Making scripts executable..."
chmod +x "$SCRIPT_DIR/start_server.py"
chmod +x "$SCRIPT_DIR/stop_server.py"

# Install required Python packages
echo "Installing required Python packages..."
pip3 install psutil

# Create systemd service file
echo "Creating systemd service file..."
cat > /tmp/office-server.service << EOF
[Unit]
Description=Office Hours Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 $SCRIPT_DIR/start_server.py
ExecStop=/usr/bin/python3 $SCRIPT_DIR/stop_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Create systemd timer file
echo "Creating systemd timer file..."
cat > /tmp/office-server.timer << EOF
[Unit]
Description=Office Hours Server Timer
Requires=office-server.service

[Timer]
# Start at 8:00 AM on weekdays
OnCalendar=Mon..Fri 08:00:00
# Stop at 6:00 PM on weekdays
OnCalendar=Mon..Fri 18:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Copy service files to systemd directory
sudo cp /tmp/office-server.service /etc/systemd/system/
sudo cp /tmp/office-server.timer /etc/systemd/system/

# Reload systemd and enable services
echo "Enabling systemd services..."
sudo systemctl daemon-reload
sudo systemctl enable office-server.service
sudo systemctl enable office-server.timer

# Create a manual control script
cat > "$SCRIPT_DIR/control_server.sh" << 'EOF'
#!/bin/bash

# Manual server control script for Linux

case "$1" in
    start)
        echo "Starting office server..."
        sudo systemctl start office-server.service
        ;;
    stop)
        echo "Stopping office server..."
        sudo systemctl stop office-server.service
        ;;
    restart)
        echo "Restarting office server..."
        sudo systemctl restart office-server.service
        ;;
    status)
        echo "Checking server status..."
        sudo systemctl status office-server.service --no-pager
        ;;
    logs)
        echo "Recent server logs:"
        sudo journalctl -u office-server.service --no-pager -n 50
        ;;
    enable-timer)
        echo "Enabling office hours timer..."
        sudo systemctl enable office-server.timer
        sudo systemctl start office-server.timer
        ;;
    disable-timer)
        echo "Disabling office hours timer..."
        sudo systemctl stop office-server.timer
        sudo systemctl disable office-server.timer
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|enable-timer|disable-timer}"
        echo ""
        echo "Commands:"
        echo "  start         - Start the office server manually"
        echo "  stop          - Stop the office server manually"
        echo "  restart       - Restart the office server"
        echo "  status        - Check server status"
        echo "  logs          - View server logs"
        echo "  enable-timer  - Enable automatic office hours scheduling"
        echo "  disable-timer - Disable automatic office hours scheduling"
        exit 1
        ;;
esac
EOF

chmod +x "$SCRIPT_DIR/control_server.sh"

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 What was installed:"
echo "  • systemd service: office-server.service"
echo "  • systemd timer: office-server.timer"
echo "  • Manual control script: ./control_server.sh"
echo ""
echo "🔧 Manual controls:"
echo "  ./control_server.sh start         - Start server manually"
echo "  ./control_server.sh stop          - Stop server manually"
echo "  ./control_server.sh restart       - Restart server"
echo "  ./control_server.sh status        - Check server status"
echo "  ./control_server.sh logs          - View server logs"
echo "  ./control_server.sh enable-timer  - Enable office hours automation"
echo "  ./control_server.sh disable-timer - Disable office hours automation"
echo ""
echo "🌐 Server will be accessible at:"
echo "  Frontend: http://[YOUR_OFFICE_IP]:3000"
echo "  Backend:  http://[YOUR_OFFICE_IP]:5000"
echo ""
echo "📝 To uninstall automation:"
echo "  sudo systemctl disable office-server.service"
echo "  sudo systemctl disable office-server.timer"
echo "  sudo rm /etc/systemd/system/office-server.service"
echo "  sudo rm /etc/systemd/system/office-server.timer"
echo "  sudo systemctl daemon-reload" 