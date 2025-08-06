# Configuration Guide

This guide explains how to configure the Xibo Screen Updater for your environment.

## Configuration File Priority

The application looks for configuration files in this order:

1. **Command line argument**: `xibo-screen-updater -c /path/to/config.yaml`
2. **Environment variable**: `CONFIG_PATH=/path/to/config.yaml`
3. **Default location**: `./config.yaml`

## Configuration File Format

The configuration uses YAML format with two main sections:

### Complete Example

```yaml
name: xibo_screen_production
copy_from: 
  provider: nextcloud
  path: Digital-Signage/Content
  auth: 
    type: basic_auth
    user: your_username
    password: your_password
  server: https://your-nextcloud.example.com
  extensions: 
    - .jpg
    - .png
    - .mp4
    - .avi
    - .pdf
  poll_interval: 30  # seconds
project_to:
  provider: xibo
  host: https://your-xibo.example.com/api/
  auth:
    type: oauth2
    grant_type: client_credentials
    client_id: your_client_id
    client_secret: your_client_secret
  display:
    name: Main Display
    width: 1920
    height: 1080
    background:
      color: '#000000'
```

## Configuration Sections

### NextCloud Configuration (`copy_from`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | string | Yes | Must be "nextcloud" |
| `server` | string | Yes | NextCloud server URL (with protocol) |
| `path` | string | Yes | Directory path to monitor in NextCloud |
| `auth.user` | string | Yes | NextCloud username |
| `auth.password` | string | Yes | NextCloud password or app password |
| `extensions` | array | Yes | File extensions to monitor (include the dot) |
| `poll_interval` | integer | No | Seconds between checks (default: 10) |

### Xibo Configuration (`project_to`)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `provider` | string | Yes | Must be "xibo" |
| `host` | string | Yes | Xibo CMS API URL (with /api/ path) |
| `auth.client_id` | string | Yes | OAuth2 client ID |
| `auth.client_secret` | string | Yes | OAuth2 client secret |
| `display.name` | string | Yes | Target display name in Xibo |
| `display.width` | integer | Yes | Display resolution width |
| `display.height` | integer | Yes | Display resolution height |
| `display.background.color` | string | No | Background color (hex format) |

## Setting Up Configuration

### Step 1: Create Configuration File

```bash
# Copy the example
cp config/example.yaml config.yaml

# Or create in a custom location
cp config/example.yaml /etc/xibo/production.yaml
```

### Step 2: Edit Configuration

Edit the configuration file with your actual values:

```bash
# Use your preferred editor
nano config.yaml
# or
vim config.yaml
# or
code config.yaml
```

### Step 3: Secure Your Configuration

```bash
# Set appropriate permissions
chmod 600 config.yaml

# For production, store outside the project directory
sudo mkdir -p /etc/xibo
sudo cp config.yaml /etc/xibo/production.yaml
sudo chown xibo:xibo /etc/xibo/production.yaml
sudo chmod 600 /etc/xibo/production.yaml
```

## Environment-Specific Configurations

### Development Configuration

```yaml
name: xibo_screen_dev
copy_from:
  server: http://localhost:8080  # Local NextCloud
  path: test-content
  poll_interval: 5  # Faster polling for testing
project_to:
  host: http://localhost:8082/api/  # Local Xibo
  display:
    name: Test Display
```

### Production Configuration

```yaml
name: xibo_screen_prod
copy_from:
  server: https://cloud.company.com
  path: digital-signage/main-lobby
  poll_interval: 60  # Less frequent polling
project_to:
  host: https://xibo.company.com/api/
  display:
    name: Lobby Display
```

## Security Best Practices

### 1. Use App Passwords

For NextCloud, create an app-specific password instead of using your main password:

1. Go to NextCloud Settings → Security
2. Create a new app password for "Xibo Screen Updater"
3. Use this password in the configuration

### 2. OAuth2 Client Setup

For Xibo, set up a dedicated OAuth2 client:

1. Go to Xibo CMS → Administration → Applications
2. Create a new application with:
   - Grant Type: Client Credentials
   - Confidential: Yes
   - Scopes: appropriate permissions for your use case

### 3. File Permissions

```bash
# Configuration files should not be world-readable
chmod 600 config.yaml

# For system-wide installation
sudo chown root:xibo /etc/xibo/production.yaml
sudo chmod 640 /etc/xibo/production.yaml
```

### 4. Environment Variables for Secrets

For extra security, you can use environment variables:

```yaml
# In config.yaml
copy_from:
  auth:
    user: "${NEXTCLOUD_USER}"
    password: "${NEXTCLOUD_PASSWORD}"
project_to:
  auth:
    client_secret: "${XIBO_CLIENT_SECRET}"
```

```bash
# Set environment variables
export NEXTCLOUD_USER="your_username"
export NEXTCLOUD_PASSWORD="your_app_password"
export XIBO_CLIENT_SECRET="your_client_secret"
```

## Configuration Validation

Test your configuration:

```bash
# Test NextCloud connection
test-nextcloud

# Test Xibo connection
test-xibo

# Test with custom config
python test_nextcloud.py  # Edit script for custom config path
python test_xibo.py       # Edit script for custom config path
```

## Common Configuration Issues

### NextCloud Issues

1. **Server URL Format**
   ```yaml
   # ✅ Correct
   server: https://cloud.example.com
   
   # ❌ Incorrect
   server: cloud.example.com  # Missing protocol
   server: https://cloud.example.com/  # Trailing slash
   ```

2. **Path Format**
   ```yaml
   # ✅ Correct
   path: folder/subfolder
   
   # ❌ Incorrect
   path: /folder/subfolder  # Leading slash
   path: folder/subfolder/  # Trailing slash
   ```

### Xibo Issues

1. **API URL Format**
   ```yaml
   # ✅ Correct
   host: https://xibo.example.com/api/
   
   # ❌ Incorrect
   host: https://xibo.example.com  # Missing /api/
   host: https://xibo.example.com/api  # Missing trailing slash
   ```

2. **Display Name**
   - Must match exactly the display name in Xibo CMS
   - Case-sensitive
   - Use the actual display name, not the display ID

## Multiple Configurations

You can maintain multiple configuration files:

```bash
# Development
xibo-screen-updater -c config/development.yaml

# Staging
xibo-screen-updater -c config/staging.yaml

# Production
xibo-screen-updater -c /etc/xibo/production.yaml
```

## Next Steps

After configuring:

1. Test your configuration with [Testing Guide](testing.md)
2. Learn about deployment options in [Deployment Guide](deployment.md)
3. Start using the application with [Usage Guide](usage.md)
