# Configuration Usage Examples

This document shows various ways to use the Xibo Screen Updater with different configuration approaches.

## Basic Usage

```bash
# Default: looks for ./config.yaml
xibo-screen-updater
```

## Custom Configuration File

```bash
# Specify config file with command line argument
xibo-screen-updater -c /path/to/your/config.yaml
xibo-screen-updater --config /path/to/your/config.yaml

# Using environment variable
export CONFIG_PATH=/path/to/your/config.yaml
xibo-screen-updater
```

## Development Usage

```bash
# Run directly with Python
python main.py -c /path/to/config.yaml

# Using Make
make run                                    # Uses ./config.yaml
make run CONFIG=/path/to/config.yaml       # Uses specific config
CONFIG_PATH=/path/to/config.yaml make run  # Uses environment variable
```

## Docker Usage

```bash
# Mount config file
docker run -v /host/path/config.yaml:/app/config.yaml xibo-screen-updater

# Mount config directory
docker run -v /host/path/configs:/app/configs xibo-screen-updater -c /app/configs/production.yaml

# Use environment variable
docker run -e CONFIG_PATH=/app/configs/production.yaml -v /host/path/configs:/app/configs xibo-screen-updater
```

## Production Deployment Examples

### Systemd Service

```ini
[Unit]
Description=Xibo Screen Updater
After=network.target

[Service]
Type=simple
User=xibo
WorkingDirectory=/opt/xibo-screen-updater
Environment=CONFIG_PATH=/etc/xibo/production.yaml
ExecStart=/opt/xibo-screen-updater/.venv/bin/xibo-screen-updater
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

### Docker Compose

```yaml
version: '3.8'
services:
  xibo-screen-updater:
    build: .
    volumes:
      - ./config/production.yaml:/app/config.yaml
      - ./logs:/app/logs
    environment:
      - CONFIG_PATH=/app/config.yaml
    restart: unless-stopped
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xibo-screen-updater
spec:
  replicas: 1
  selector:
    matchLabels:
      app: xibo-screen-updater
  template:
    metadata:
      labels:
        app: xibo-screen-updater
    spec:
      containers:
      - name: xibo-screen-updater
        image: xibo-screen-updater:latest
        env:
        - name: CONFIG_PATH
          value: /app/config/production.yaml
        volumeMounts:
        - name: config
          mountPath: /app/config
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: config
        configMap:
          name: xibo-config
      - name: logs
        emptyDir: {}
```

## Configuration File Locations

The application looks for configuration files in this priority order:

1. **Command line argument**: `-c /path/to/config.yaml`
2. **Environment variable**: `CONFIG_PATH=/path/to/config.yaml`
3. **Default location**: `./config.yaml`

## Multiple Environment Setup

```bash
# Development
cp config/example.yaml config/development.yaml
xibo-screen-updater -c config/development.yaml

# Staging
cp config/example.yaml config/staging.yaml
xibo-screen-updater -c config/staging.yaml

# Production
cp config/example.yaml /etc/xibo/production.yaml
xibo-screen-updater -c /etc/xibo/production.yaml
```

## Troubleshooting Configuration

```bash
# Test which config file is being used
xibo-screen-updater --help  # Shows usage information

# Verify config file syntax
python -c "import yaml; print(yaml.safe_load(open('config.yaml')))"

# Run with debug output
python main.py -c config.yaml  # Will show any config loading errors
```
