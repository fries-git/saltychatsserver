# Production Deployment

How to deploy OriginChats to a production server.

---

## Quick Start

1. **Set up server** - Linux (Ubuntu/Debian) recommended
2. **Install Python** - Python 3.8+
3. **Configure OriginChats** - Edit config.json
4. **Use a process manager** - Keep it running
5. **Set up reverse proxy** - Add SSL/HTTPS
6. **Secure the server** - Firewall, backups

---

## 1. Server Setup

### Requirements

- Linux server (Ubuntu 20.04+ recommended)
- Python 3.8 or higher
- At least 512MB RAM
- Open port for WebSocket (default: 5613)

### Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3 python3-pip -y

# Install pip packages
pip3 install -r requirements.txt
```

---

## 2. Configuration

### Basic Config

Edit `config.json`:

```json
{
  "websocket": {
    "host": "0.0.0.0",
    "port": 5613
  },
  "server": {
    "name": "My Server",
    "url": "https://chat.example.com"
  },
  "rate_limiting": {
    "enabled": true,
    "messages_per_minute": 30,
    "burst_limit": 5,
    "cooldown_seconds": 60
  }
}
```

### Key Changes for Production

- Set `host` to `"0.0.0.0"` (listen on all interfaces)
- Set `server.url` to your public URL
- Enable rate limiting
- Adjust limits as needed

---

## 3. Process Manager

Use systemd to keep OriginChats running.

### Create Service File

```bash
sudo nano /etc/systemd/system/originchats.service
```

Content:

```
[Unit]
Description=OriginChats Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/originChats
ExecStart=/usr/bin/python3 init.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable originchats
sudo systemctl start originchats

# Check status
sudo systemctl status originchats

# View logs
sudo journalctl -u originchats -f
```

---

## 4. Reverse Proxy (nginx)

Use nginx to add SSL and forward connections.

### Install nginx

```bash
sudo apt install nginx -y
```

### Configuration

Create `/etc/nginx/sites-available/originchats`:

```nginx
server {
    listen 80;
    server_name chat.example.com;

    location / {
        proxy_pass http://127.0.0.1:5613;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_read_timeout 86400;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/originchats /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 5. SSL Certificate (Let's Encrypt)

### Install Certbot

```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Get Certificate

```bash
sudo certbot --nginx -d chat.example.com
```

Certbot will:
- Get SSL certificate
- Configure nginx for HTTPS
- Set up auto-renewal

---

## 6. Firewall

### UFW Setup

```bash
sudo apt install ufw

# Allow SSH
sudo ufw allow ssh

# Allow HTTP/HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Or allow WebSocket port directly
sudo ufw allow 5613/tcp

sudo ufw enable
```

---

## 7. Backups

### Backup Script

Create `/opt/backup-originchats.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backup/originchats"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database files
tar -czf $BACKUP_DIR/db_$DATE.tar.gz /opt/originChats/db/

# Keep only last 7 days
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
```

### Cron Job

```bash
crontab -e

# Add line to backup daily at 2am
0 2 * * * /opt/backup-originchats.sh
```

---

## 8. Monitoring

### Check Logs

```bash
# Service logs
sudo journalctl -u originchats -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Health Check Script

Create `/opt/health-check.sh`:

```bash
#!/bin/bash

if ! systemctl is-active --quiet originchats; then
    echo "OriginChats is down, restarting..."
    sudo systemctl restart originchats
fi
```

### Cron Health Check

```bash
# Check every 5 minutes
*/5 * * * * /opt/health-check.sh
```

---

## 9. Security Checklist

- [ ] Change default port (or use firewall to restrict)
- [ ] Enable rate limiting
- [ ] Use HTTPS (SSL certificate)
- [ ] Run as non-root user
- [ ] Set up firewall (UFW)
- [ ] Keep system updated
- [ ] Regular backups
- [ ] Monitor logs for suspicious activity

---

## 10. Performance Tuning

### System Limits

Edit `/etc/security/limits.conf`:

```
* soft nofile 65535
* hard nofile 65535
```

### Nginx Tuning

Edit `/etc/nginx/nginx.conf`:

```nginx
worker_processes auto;
events {
    worker_connections 1024;
}
```

---

## 11. Updating

### Update Process

```bash
# Stop server
sudo systemctl stop originchats

# Pull changes
cd /opt/originChats
git pull

# Update dependencies
pip3 install -r requirements.txt --upgrade

# Start server
sudo systemctl start originchats
```

---

## 12. Troubleshooting

### Server Won't Start

```bash
# Check if port is in use
sudo lsof -i :5613

# Check logs
sudo journalctl -u originchats -n 50
```

### Can't Connect

1. Check firewall: `sudo ufw status`
2. Check if server is running: `sudo systemctl status originchats`
3. Check nginx: `sudo nginx -t`
4. Check SSL: `sudo certbot certificates`

### WebSocket Disconnects

- Check nginx timeout settings
- Check proxy configuration
- Check client-side connection handling

---

## Docker (Alternative)

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5613
CMD ["python", "init.py"]
```

### Run

```bash
docker build -t originchats .
docker run -d -p 5613:5613 -v $(pwd)/db:/app/db originchats
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Start server | `sudo systemctl start originchats` |
| Stop server | `sudo systemctl stop originchats` |
| Restart server | `sudo systemctl restart originchats` |
| View logs | `sudo journalctl -u originchats -f` |
| Check status | `sudo systemctl status originchats` |
| Test nginx | `sudo nginx -t` |
| Renew SSL | `sudo certbot renew` |

---

## Next Steps

- Set up monitoring (Prometheus, Grafana)
- Add log aggregation (Loki, ELK)
- Configure alerts for downtime
- Regular security audits
