# IDSCNR Production Deployment Guide

Complete guide for deploying IDSCNR to production environments.

---

## 📋 Prerequisites

### System Requirements

- **Server**: Linux (Ubuntu 20.04+ recommended), Windows Server, or macOS
- **RAM**: 2GB minimum, 4GB+ recommended
- **Disk Space**: 10GB+ for application and image storage
- **CPU**: 2+ cores recommended
- **Network**: Static IP or domain name

### Software Requirements

- **Docker & Docker Compose** (recommended) OR
- **Python 3.11+** and **Node.js 18+** (manual deployment)
- **Tesseract OCR** installed on the system
- **Reverse Proxy** (nginx/Apache) for HTTPS (production)

---

## 🚀 Deployment Options

### Option 1: Docker Compose (Recommended)

#### Step 1: Install Tesseract OCR

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev
```

**CentOS/RHEL:**
```bash
sudo yum install -y tesseract tesseract-langpack-eng
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH.

#### Step 2: Clone and Configure

```bash
# Clone repository
git clone https://github.com/vrajkumarpatel/ID_Scnr.git
cd ID_Scnr

# Create .env file
cat > .env << EOF
# Security - CHANGE THESE IN PRODUCTION!
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Database
DATABASE_URL=sqlite:///./data/guestdb.sqlite

# CORS - Update with your domain
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Environment
DEBUG=false
LOG_LEVEL=INFO
EOF
```

#### Step 3: Build and Start

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Step 4: Verify Deployment

```bash
# Check backend health
curl http://localhost:8000/health

# Check OCR health
curl http://localhost:8000/ocr/health

# Access frontend
# Open http://your-server-ip:5173 in browser
```

---

### Option 2: Manual Deployment

#### Step 1: Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y \
    python3.11 python3.11-venv python3-pip \
    nodejs npm \
    tesseract-ocr tesseract-ocr-eng libtesseract-dev \
    nginx \
    sqlite3
```

#### Step 2: Backend Setup

```bash
cd /opt/idscnr/backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Set environment variables
export JWT_SECRET=$(openssl rand -hex 32)
export ENCRYPTION_KEY=$(openssl rand -hex 32)
export DEBUG=false

# Test run (run from project root)
cd /opt/idscnr
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

#### Step 3: Frontend Setup

```bash
cd /opt/idscnr/frontend

# Install dependencies
npm install

# Build for production
npm run build

# Serve with nginx (see nginx configuration below)
```

#### Step 4: Create Systemd Service

Create `/etc/systemd/system/idscnr-backend.service`:

```ini
[Unit]
Description=IDSCNR Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/idscnr
Environment="PATH=/opt/idscnr/backend/venv/bin"
Environment="JWT_SECRET=your-secret-here"
Environment="ENCRYPTION_KEY=your-key-here"
Environment="DEBUG=false"
ExecStart=/opt/idscnr/backend/venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable idscnr-backend
sudo systemctl start idscnr-backend
sudo systemctl status idscnr-backend
```

---

## 🔒 Security Configuration

### 1. Environment Variables

**NEVER** commit `.env` files to version control. Use environment variables or secrets management:

```bash
# Generate secure secrets
JWT_SECRET=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(openssl rand -hex 32)

# Store in environment or secrets manager
export JWT_SECRET
export ENCRYPTION_KEY
```

### 2. HTTPS Setup with Nginx

Create `/etc/nginx/sites-available/idscnr`:

```nginx
# Backend API
upstream idscnr_backend {
    server localhost:8000;
}

# Frontend
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL certificates (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend
    location / {
        root /opt/idscnr/frontend/dist;
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache";
    }

    # Backend API
    location /api {
        proxy_pass http://idscnr_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # CORS headers
        add_header Access-Control-Allow-Origin $http_origin always;
        add_header Access-Control-Allow-Credentials true always;
        add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/idscnr /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Firewalld (CentOS/RHEL)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 4. SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## 📊 Monitoring and Maintenance

### Health Checks

```bash
# Backend health
curl https://yourdomain.com/api/health

# OCR health
curl https://yourdomain.com/api/ocr/health
```

### Logs

**Docker:**
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

**Systemd:**
```bash
sudo journalctl -u idscnr-backend -f
```

**Application logs:**
```bash
tail -f /opt/idscnr/backend/data/app.log
```

### Database Backups

```bash
# Create backup script
cat > /opt/idscnr/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/idscnr/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
cp /opt/idscnr/backend/data/guestdb.sqlite $BACKUP_DIR/db_$DATE.sqlite

# Backup encrypted images
tar -czf $BACKUP_DIR/images_$DATE.tar.gz /opt/idscnr/scans

# Keep only last 30 days
find $BACKUP_DIR -name "*.sqlite" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
EOF

chmod +x /opt/idscnr/backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/idscnr/backup.sh") | crontab -
```

### Performance Monitoring

- Monitor API response times
- Track OCR processing times
- Monitor database size and query performance
- Set up alerts for errors and high resource usage

---

## 🔄 Updates and Maintenance

### Updating the Application

**Docker:**
```bash
cd /opt/idscnr
git pull origin main
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

**Manual:**
```bash
cd /opt/idscnr
git pull origin main

# Backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart idscnr-backend

# Frontend
cd ../frontend
npm install
npm run build
sudo systemctl reload nginx
```

### Database Migrations

The application handles database migrations automatically on startup. For manual migrations:

```bash
cd /opt/idscnr
/opt/idscnr/backend/venv/bin/python -c "from backend.database import init_db; init_db()"
```

---

## 🆘 Troubleshooting

### Common Issues

#### 1. OCR Not Working

**Symptoms:** OCR health check fails, no text extracted

**Solutions:**
```bash
# Verify Tesseract installation
tesseract --version

# Check Tesseract data path
echo $TESSDATA_PREFIX

# Test OCR manually
tesseract test_image.png stdout

# Check backend logs
docker-compose logs backend | grep -i ocr
```

#### 2. Database Errors

**Symptoms:** Application fails to start, database locked

**Solutions:**
```bash
# Check database file permissions
ls -la /opt/idscnr/backend/data/guestdb.sqlite

# Fix permissions
sudo chown www-data:www-data /opt/idscnr/backend/data/guestdb.sqlite
sudo chmod 664 /opt/idscnr/backend/data/guestdb.sqlite

# Check for locks
fuser /opt/idscnr/backend/data/guestdb.sqlite
```

#### 3. Image Encryption Errors

**Symptoms:** Images fail to decrypt, encryption errors in logs

**Solutions:**
```bash
# Verify encryption key is set
echo $ENCRYPTION_KEY

# Check key consistency (must be same across restarts)
# Regenerate keys will make existing encrypted images unreadable
```

#### 4. CORS Errors

**Symptoms:** Frontend can't connect to backend

**Solutions:**
- Verify CORS_ORIGINS includes your frontend domain
- Check nginx proxy configuration
- Verify backend CORS middleware settings

#### 5. High Memory Usage

**Symptoms:** Server becomes slow, out of memory errors

**Solutions:**
```bash
# Monitor memory
free -h
docker stats

# Clean up temporary files
find /opt/idscnr/backend/temp -type f -mtime +1 -delete

# Restart services
docker-compose restart
# or
sudo systemctl restart idscnr-backend
```

---

## 📞 Support

For deployment issues:

1. Check application logs: `backend/data/app.log`
2. Review system logs: `journalctl -u idscnr-backend`
3. Test health endpoints: `/health`, `/ocr/health`
4. Verify Tesseract installation: `tesseract --version`
5. Check environment variables are set correctly
6. Review firewall and network configuration

---

## ✅ Production Checklist

Before going live, ensure:

- [ ] Strong JWT_SECRET and ENCRYPTION_KEY set
- [ ] HTTPS/SSL certificates configured
- [ ] Reverse proxy (nginx) configured
- [ ] Firewall rules configured
- [ ] Database backups automated
- [ ] Log rotation configured
- [ ] Monitoring and alerts set up
- [ ] CORS origins restricted to your domain
- [ ] DEBUG mode disabled
- [ ] Admin PIN set
- [ ] Tesseract OCR verified working
- [ ] Health checks passing
- [ ] Test scan and OCR processing
- [ ] Test DNR matching
- [ ] Test guest management workflow

---

**Last Updated:** 2025-01-XX  
**Maintained by:** Vrajkumar Patel
