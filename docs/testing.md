# Testing Guide

This guide explains how to test your Xibo Screen Updater installation and configuration.

## Testing Your Installation

### Basic Installation Test

```bash
# Test that all modules can be imported
python -c "import main, nextcloud_client, xibo_client; print('✅ All modules imported successfully')"

# Test console scripts are available
xibo-screen-updater --help
test-nextcloud --help
test-xibo --help
```

### Docker Environment Test

Test in a clean environment to ensure the setup works:

```bash
# Test the setup script
make test-docker

# Manual Docker test
docker run -it --rm -v $(pwd):/app -w /app python:3.12 bash -c "chmod +x setup.sh && ./setup.sh"
```

## Testing Connections

### NextCloud Connection Test

```bash
# Using the test script (uses config/example.yaml)
test-nextcloud

# Or run directly
python test_nextcloud.py
```

**Expected Output:**
```
Testing NextCloud client...
--------------------------------------------------
1. Testing server connection...
✅ Server connection successful!

2. Getting file list...
✅ Found X files in directory
   - file1.jpg (1.2 MB)
   - file2.png (800 KB)
   ...

✅ All tests passed! NextCloud client is working correctly.
```

### Xibo Connection Test

```bash
# Using the test script (uses config/example.yaml)
test-xibo

# Or run directly
python test_xibo.py
```

**Expected Output:**
```
Testing Xibo client...
--------------------------------------------------
1. Testing authentication...
✅ Authentication successful!

2. Getting server information...
✅ Server info retrieved:
   Version: 3.3.0
   Build: 123

3. Getting displays...
✅ Found X displays:
   - Display 1 (ID: 1)
   - Display 2 (ID: 2)
   ...

✅ All tests passed! Xibo client is working correctly.
```

## Custom Configuration Testing

The test scripts currently use `config/example.yaml`. To test with your actual configuration:

### Option 1: Modify Test Scripts

Edit the test scripts to use your config file:

```python
# In test_nextcloud.py or test_xibo.py
config = load_config("config.yaml")  # Change this line
```

### Option 2: Copy Your Config

```bash
# Temporarily copy your config for testing
cp config.yaml config/example.yaml
test-nextcloud
test-xibo
# Don't forget to restore the original example.yaml
```

### Option 3: Create Custom Test Scripts

```python
#!/usr/bin/env python3
"""Custom test script for your configuration."""

import yaml
import sys
from nextcloud_client import NextCloudClient
from xibo_client import create_xibo_client_from_config

def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def test_with_custom_config():
    config_path = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    config = load_config(config_path)
    
    # Test NextCloud
    print("Testing NextCloud...")
    nc_config = config['copy_from']
    client = NextCloudClient(
        nc_config['server'],
        nc_config['auth']['user'],
        nc_config['auth']['password']
    )
    files = client.get_files(nc_config['path'], nc_config['extensions'])
    print(f"✅ Found {len(files)} files")
    
    # Test Xibo
    print("Testing Xibo...")
    xibo_client = create_xibo_client_from_config(config, debug=True)
    if xibo_client.authenticate():
        print("✅ Xibo authentication successful")
    else:
        print("❌ Xibo authentication failed")

if __name__ == "__main__":
    test_with_custom_config()
```

## Integration Testing

### End-to-End Test

Test the complete workflow with a test file:

```bash
# 1. Place a test image in your NextCloud folder
# 2. Run the application in test mode (short duration)
# 3. Verify the file appears in Xibo

# Create a test config with short poll interval
cp config.yaml config/test.yaml
# Edit config/test.yaml to set poll_interval: 5

# Run for a short time
timeout 30s xibo-screen-updater -c config/test.yaml
```

### Manual Integration Test

1. **Prepare Test File**
   ```bash
   # Create or copy a test image
   cp /path/to/test/image.jpg ~/test-image.jpg
   ```

2. **Upload to NextCloud**
   - Upload the test file to your configured NextCloud path
   - Note the upload time

3. **Monitor Application**
   ```bash
   # Run the application and watch for the file
   xibo-screen-updater -c config.yaml
   ```

4. **Verify in Xibo**
   - Check Xibo CMS media library for the uploaded file
   - Verify the layout was created
   - Check that it's scheduled on the target display

## Performance Testing

### File Processing Speed

Test how quickly files are processed:

```bash
# Upload multiple test files to NextCloud
# Monitor application logs for processing times
# Check system resources during processing
```

### Large File Testing

Test with different file sizes:

```bash
# Test with various file sizes:
# - Small images (< 1MB)
# - Medium images (1-10MB)  
# - Large images (10-50MB)
# - Video files (if supported)
```

## Troubleshooting Tests

### Common Test Failures

1. **NextCloud Connection Fails**
   ```
   ❌ Error: Connection refused
   ```
   - Check server URL and network connectivity
   - Verify credentials
   - Check NextCloud server status

2. **Xibo Authentication Fails**
   ```
   ❌ Authentication failed: Invalid client credentials
   ```
   - Verify OAuth2 client ID and secret
   - Check Xibo server URL
   - Ensure OAuth2 client is active in Xibo

3. **File Not Found**
   ```
   ❌ No files found in directory
   ```
   - Check NextCloud path configuration
   - Verify file extensions match
   - Ensure files exist in the specified directory

### Debug Mode

Enable debug output for more detailed testing:

```python
# In test scripts or main application
xibo_client = create_xibo_client_from_config(config, debug=True)
```

### Network Testing

Test network connectivity:

```bash
# Test NextCloud server
curl -I https://your-nextcloud.example.com

# Test Xibo server
curl -I https://your-xibo.example.com/api/

# Test with authentication
curl -u username:password https://your-nextcloud.example.com/remote.php/dav/
```

## Automated Testing

### Unit Tests

Run the included unit tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/unit/test_config_manager.py -v
```

### Integration Tests

Run integration tests (require configuration):

```bash
# Run integration tests
pytest tests/integration/ -v

# Run specific integration test
pytest tests/integration/test_nextcloud_provider.py -v
```

### Continuous Testing

Set up automated testing with Make:

```bash
# Run all quality checks
make check-all

# Run tests
make test

# Test connections
make test-connections
```

## Test Reports

### Generate Test Coverage

```bash
# Install coverage tools
pip install pytest-cov

# Run tests with coverage
pytest --cov=. --cov-report=html

# View coverage report
open htmlcov/index.html
```

### Performance Reports

Monitor application performance:

```bash
# Monitor resource usage
top -p $(pgrep -f xibo-screen-updater)

# Monitor network traffic
sudo netstat -tuln | grep :80

# Check disk usage
df -h
du -sh logs/
```

## Next Steps

After successful testing:

1. Learn about deployment options in [Deployment Guide](deployment.md)
2. Start using the application with [Usage Guide](usage.md)
3. Monitor your deployment with [Monitoring Guide](monitoring.md)
