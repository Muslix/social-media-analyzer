#!/bin/bash
# Setup systemd service for Truth Social Market Analyzer

set -e

echo "🚀 Setting up systemd service..."

# Copy service file to systemd
sudo cp social-media-analyzer.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable social-media-analyzer

# Start service
sudo systemctl start social-media-analyzer

echo ""
echo "✅ Service installed and started!"
echo ""
echo "📋 Useful commands:"
echo "  sudo systemctl status social-media-analyzer   # Check status"
echo "  sudo systemctl stop social-media-analyzer     # Stop service"
echo "  sudo systemctl start social-media-analyzer    # Start service"
echo "  sudo systemctl restart social-media-analyzer  # Restart service"
echo "  sudo journalctl -u social-media-analyzer -f   # View logs (follow)"
echo "  sudo journalctl -u social-media-analyzer -n 100  # Last 100 lines"
