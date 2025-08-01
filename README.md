# Xibo Screen Updater

A Python application that monitors a NextCloud directory for new files and automatically uploads them to Xibo CMS, setting them as default content for specified displays.

## Features

- **NextCloud Integration**: Monitors NextCloud directories via WebDAV
- **Xibo CMS Integration**: Uploads media and manages display layouts via OAuth2 API
- **Real-time Monitoring**: Polls for new files at configurable intervals
- **Automatic Processing**: Downloads, uploads, and sets content as default for displays
- **File Type Filtering**: Supports multiple media formats (images, videos, PDFs)
- **Robust Error Handling**: Comprehensive logging and error recovery

## Supported File Formats

- Images: `.jpg`, `.png`
- Videos: `.mp4`, `.avi`
- Documents: `.pdf`

## Requirements

- Python 3.8+
- NextCloud server with WebDAV access
- Xibo CMS with API access
- OAuth2 credentials for Xibo

## Installation

### Using pip

```bash
# Install the package
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Using Poetry (if you prefer)

```bash
poetry install
```

## Configuration

Create a configuration file at `config/example.yaml`:

```yaml
name: xibo_screen_1
copy_from: 
  provider: nextcloud
  path: Xibo
  auth: 
    type: basic_auth
    user: admin
    password: admin_password
  server: http://localhost:8080
  extensions: 
    - .jpg
    - .png
    - .mp4
    - .avi
    - .pdf
  poll_interval: 10  # seconds
project_to:
  provider: xibo
  host: http://localhost:8082/api/
  auth:
    type: oauth2
    grant_type: client_credentials
    client_id: your_client_id
    client_secret: your_client_secret
  display:
    name: Display Name
    width: 1920
    height: 1080
    background:
      color: '#000000'
```

### Configuration Options

#### NextCloud Settings (`copy_from`)
- `server`: NextCloud server URL
- `path`: Directory path to monitor
- `auth.user`: Username for NextCloud
- `auth.password`: Password for NextCloud
- `extensions`: List of file extensions to monitor
- `poll_interval`: How often to check for new files (seconds)

#### Xibo Settings (`project_to`)
- `host`: Xibo CMS API endpoint
- `auth.client_id`: OAuth2 client ID
- `auth.client_secret`: OAuth2 client secret
- `display.name`: Target display name
- `display.width`: Display resolution width
- `display.height`: Display resolution height
- `display.background.color`: Background color for layouts

## Usage

### Running the Main Application

```bash
# Using the installed script
xibo-screen-updater

# Or directly with Python
python main.py
```

### Testing Connections

Test your NextCloud connection:
```bash
test-nextcloud
# Or: python test_nextcloud.py
```

Test your Xibo connection:
```bash
test-xibo
# Or: python test_xibo.py
```

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/71walceli/XiboScreenUpdater.git
cd XiboScreenUpdater

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest test_xibo.py -v
```

### Code Formatting

```bash
# Format code with Black
black .

# Check with flake8
flake8 .

# Type checking with MyPy
mypy .
```

## Project Structure

```
├── main.py              # Main application entry point
├── nextcloud_client.py  # NextCloud WebDAV client
├── xibo_client.py       # Xibo CMS API client
├── test_nextcloud.py    # NextCloud connection tests
├── test_xibo.py         # Xibo connection tests
├── config/
│   └── example.yaml     # Configuration template
├── data/                # Test data and screenshots
├── pyproject.toml       # Project configuration
└── README.md           # This file
```

## How It Works

1. **Monitor**: The application continuously polls the configured NextCloud directory
2. **Detect**: When new files are detected (based on upload timestamp)
3. **Download**: Files are downloaded to a temporary directory
4. **Upload**: Files are uploaded to Xibo's media library
5. **Layout**: A new layout is created with the uploaded media
6. **Schedule**: The layout is set as default content for the specified display
7. **Cleanup**: Temporary files are removed

## API Documentation

### NextCloudClient

```python
from nextcloud_client import NextCloudClient

client = NextCloudClient(server_url, username, password)
files = client.get_files(directory_path, extensions)
local_path = client.download_file(remote_path, local_path)
```

### XiboClient

```python
from xibo_client import create_xibo_client_from_config

client = create_xibo_client_from_config(config)
client.authenticate()
success = client.upload_and_set_screen(file_path, screen_name)
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Check your NextCloud/Xibo credentials
   - Verify server URLs are accessible
   - Ensure OAuth2 client has proper permissions

2. **Files Not Detected**
   - Check file extensions match configuration
   - Verify NextCloud path exists and is accessible
   - Check poll interval settings

3. **Upload Failures**
   - Verify Xibo API permissions
   - Check file size limits
   - Ensure display name exists in Xibo

### Debug Mode

Enable debug output by modifying the client creation:

```python
xibo_client = create_xibo_client_from_config(config, debug=True)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue on the GitHub repository or contact the maintainers.
