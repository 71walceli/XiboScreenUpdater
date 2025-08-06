
# Xibo Screen Updater - Architecture Overview

This document describes the current architecture of the Xibo Screen Updater system, designed to monitor NextCloud directories and automatically upload new files to Xibo CMS displays.

## System Architecture

The system follows a **polling-based monitoring architecture** with the following key characteristics:

- **Single-instance operation**: Each instance monitors one NextCloud directory and targets one Xibo display
- **Configuration-driven**: All behavior controlled via YAML configuration files
- **Provider pattern**: Pluggable architecture for different source/destination providers
- **Synchronous processing**: Sequential processing of files with comprehensive error handling

## Core Components

### 1. Main Controller (`main.py`)
**Role**: Application orchestrator and main workflow controller

**Responsibilities**:
- Configuration loading with multiple resolution strategies (CLI argument > environment variable > default location)
- Main monitoring loop with configurable polling intervals
- File detection and processing coordination
- Error handling and recovery
- Temporary file management and cleanup
- Process state tracking (tracks latest upload timestamp)

**Architecture Pattern**: Controller pattern with dependency injection of client providers

**Key Workflows**:
```
Startup → Load Config → Initialize Clients → Start Monitor Loop
Monitor Loop: Poll → Detect New Files → Download → Upload → Schedule → Cleanup → Sleep → Repeat
```

### 2. Configuration Management
**Role**: Centralized configuration handling

**Features**:
- **Hierarchical loading**: CLI args → ENV vars → default file (`./config.yaml`)
- **YAML-based**: Human-readable configuration format
- **Provider abstraction**: Configurable source and destination providers
- **Validation**: Basic configuration validation during load
- **Flexible paths**: Support for relative and absolute configuration file paths

**Configuration Structure**:
```yaml
copy_from:          # Source provider configuration
  provider: nextcloud
  auth: {...}
  server: "..."
  path: "..."
  extensions: [...]
  poll_interval: 10

project_to:         # Destination provider configuration
  provider: xibo
  auth: {...}
  host: "..."
  display: {...}
```

### 3. Source Provider - NextCloud Client (`nextcloud_client.py`)
**Role**: WebDAV-based file system interface for NextCloud

**Architecture Pattern**: Client/Adapter pattern implementing WebDAV protocol

**Key Features**:
- **WebDAV Integration**: Full PROPFIND/GET support for file operations
- **Metadata Extraction**: File timestamps, sizes, content types, ETags
- **Extension Filtering**: Configurable file type filtering
- **Connection Management**: Persistent HTTP Basic Auth sessions
- **Error Handling**: Network retry logic with exponential backoff
- **Namespace Support**: XML namespace handling for NextCloud-specific properties

**API Design**:
```python
class NextCloudClient:
    def get_files(directory_path, extensions) -> List[FileInfo]
    def download_file(file_path, local_path) -> str
    def list_files(directory_path, extensions) -> List[Dict]
```

**File Detection Strategy**: 
- Uses NextCloud's `upload_time` property for new file detection
- Maintains timestamp-based state to avoid reprocessing files
- Timezone-aware datetime handling (converts to UTC)

### 4. Destination Provider - Xibo Client (`xibo_client.py`)
**Role**: Xibo CMS API interface for media management and display scheduling

**Architecture Pattern**: Client/Facade pattern abstracting complex Xibo workflows

**Authentication**: OAuth2 Client Credentials flow with automatic token refresh

**Key Workflows**:

1. **Media Upload Workflow**:
   ```
   Upload File → Get Media ID → Return Media Object
   ```

2. **Complete Screen Update Workflow**:
   ```
   Upload Media → Create Fullscreen Layout → Schedule to Display Group → Delete Old Schedules → Force Display Refresh
   ```

**API Design**:
```python
class XiboClient:
    # Core Operations
    def authenticate() -> bool
    def upload_media(file_path, name, tags) -> Dict
    
    # Layout Management
    def create_fullscreen_layout(media_id, name) -> Dict
    def get_layouts(layout_name) -> List[Dict]
    
    # Display Management
    def get_displays(display_name) -> List[Dict]
    def find_display_by_name(display_name) -> Optional[Dict]
    
    # Scheduling
    def schedule_media_relative(media_id, display_groups, hours, duration) -> Dict
    def delete_auto_scheduled_events(display_group_id) -> int
    
    # High-level Workflow
    def upload_and_set_screen(file_path, screen_name, duration_hours) -> bool
```

**Resource Management**:
- **Media Library**: Centralized media storage
- **Layouts**: Container for media arrangement (uses fullscreen layouts)
- **Campaigns**: Auto-generated from fullscreen layouts
- **Display Groups**: Targeting mechanism for displays
- **Schedule Events**: Time-based content scheduling with priority support

### 5. Testing & Validation System
**Role**: Connection testing and system validation

**Components**:
- **`test_nextcloud.py`**: NextCloud connectivity and file listing tests
- **`test_xibo.py`**: Xibo authentication, API access, and workflow tests
- **Setup Scripts**: Environment validation and dependency checking

**Testing Strategy**:
- Connection validation before main application start
- Full workflow testing including upload and scheduling
- Clean environment testing via Docker containers

## Data Flow Architecture

```
[NextCloud Directory] 
        ↓ (WebDAV PROPFIND)
[File Detection & Metadata]
        ↓ (WebDAV GET)
[Local Download (Temporary)]
        ↓ (OAuth2 API POST)
[Xibo Media Upload]
        ↓ (Layout Creation)
[Fullscreen Layout + Campaign]
        ↓ (Scheduling API)
[Display Group Schedule]
        ↓ (Cleanup & Refresh)
[Active Display Content]
```

## Error Handling & Resilience

### Error Categories & Strategies:

1. **Configuration Errors**: Fail-fast with clear error messages
2. **Network Errors**: Retry with exponential backoff (NextCloud downloads)
3. **Authentication Errors**: Token refresh for Xibo, credential validation
4. **API Errors**: Detailed logging with response status codes
5. **File System Errors**: Temporary directory cleanup and recreation
6. **Processing Errors**: Continue with next file, comprehensive logging

### Monitoring & Observability:
- Console logging with timestamps and severity levels
- Error context preservation with stack traces
- Process state tracking (files processed, success/failure counts)
- Debug mode available for troubleshooting

## Deployment Architecture

### Single-Instance Model:
- One application instance per NextCloud directory + Xibo display combination
- Configuration file per instance
- Independent process lifecycle

### Configuration Management:
- Environment-specific configuration files
- Multiple deployment options (systemd, Docker, Kubernetes)
- Flexible configuration path resolution

### Scalability Considerations:
- **Horizontal**: Multiple instances for different directories/displays
- **Vertical**: Configurable polling intervals and batch processing
- **Resource**: Temporary file cleanup and memory management

## Security Architecture

### Authentication:
- **NextCloud**: HTTP Basic Auth over HTTPS
- **Xibo**: OAuth2 Client Credentials with token refresh
- **Credential Storage**: Configuration files (not environment variables for production)

### Data Protection:
- Temporary file cleanup after processing
- No persistent credential caching
- HTTPS-only communication (configurable)

## Technology Stack & Dependencies

### Core Dependencies:
- **Python 3.8+**: Runtime environment
- **requests**: HTTP client for API communications
- **PyYAML**: Configuration file parsing
- **xml.etree.ElementTree**: WebDAV XML response parsing

### Development Dependencies:
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Code linting  
- **mypy**: Type checking
- **pre-commit**: Git hooks for code quality

## Architecture Strengths

1. **Simplicity**: Clear separation of concerns, easy to understand
2. **Reliability**: Comprehensive error handling and retry logic
3. **Flexibility**: Provider pattern allows for different source/destination types
4. **Testability**: Isolated components with dedicated test suites
5. **Maintainability**: Well-documented with consistent patterns

## Architecture Limitations & Improvement Opportunities

1. **Performance**: Sequential file processing (could benefit from parallel processing)
2. **Scalability**: Single-instance model limits throughput
3. **Real-time**: Polling-based detection has inherent latency
4. **Media Processing**: No built-in media transformation (mentioned in original docs but not implemented)
5. **State Management**: File state tracking is memory-based (not persistent across restarts)
6. **Configuration**: No runtime configuration updates (requires restart)
7. **Monitoring**: Limited observability and metrics collection

## Future Architecture Considerations

This architecture provides a solid foundation for:
- **Media processing pipeline**: 
    - Image/video transformation capabilities  
    - PDF to Image transformation for better compatibility
- **Multi-tenant operation**: Single instance handling multiple directory/display pairs
- **Advanced scheduling**: More sophisticated content scheduling logic
- **Monitoring integration**: Metrics collection and alerting
- **Provider abstraction**: Decouple single-provider just for Nextcloud & Xibo, to use providers as necessary by using runtime check of providers.
- **Basic State persistance**: 
    - Persist access tokens to avoid having to get newer tokens.
- **Unified logging**: Robust logging, with timestamps, component, and message levels.
- **Robust folder structure**: Better file hierarchy & structure
- **Test cases**: Unit tests, to ensure code quality and prevent technical debt.

