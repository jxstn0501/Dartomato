# Overview

DartsMind is a web-based application designed to process darts game screenshots and extract scoring data. The system uploads images of DartsMind game screens to a third-party ParseExtract API for optical character recognition (OCR) and text extraction, then normalizes the extracted data into a structured format for darts game analysis. The application supports multiplayer games (up to 7 players) and stores both raw and processed data for later retrieval and analysis.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
- **Web Interface**: Simple HTML/CSS/JavaScript single-page application served from the `/web` directory
- **UI Components**: Configuration form for ParseExtract API settings, file upload interface, and results display
- **Static File Serving**: Flask serves static files directly from the web directory

## Backend Architecture
- **Web Framework**: Flask-based REST API with CORS enabled for cross-origin requests
- **Application Structure**: Modular design with separate modules for different concerns:
  - `storage.py`: Database operations and data persistence
  - `parseextract_client.py`: External API integration
  - `normalizer.py`: Data transformation and standardization
  - `config_store.py`: Configuration management
- **Error Handling**: Custom exception classes for API errors with appropriate HTTP status codes

## Data Storage Solutions
- **Database**: SQLite for local data persistence
- **Schema**: Single `ingests` table storing:
  - Metadata (filename, timestamps, player names)
  - Raw API responses from ParseExtract
  - Normalized game data
  - Game settings (bust rules)
- **File Storage**: JSON-based configuration file for API settings

## Authentication and Authorization
- **Session Management**: Basic Flask session secret for development
- **API Security**: No authentication implemented (development/testing setup)
- **CORS Policy**: Permissive CORS allowing all origins for development

## Data Processing Pipeline
- **Image Upload**: Accepts JPEG/PNG files via multipart form data
- **OCR Processing**: Forwards images to ParseExtract API for text extraction
- **Data Normalization**: Converts raw OCR results into standardized darts game format
- **Persistence**: Stores both raw and processed data for audit trails

## Configuration Management
- **Environment Variables**: Primary configuration through environment variables
- **JSON Config**: Fallback configuration stored in local JSON file
- **Stub Mode**: Development mode that bypasses external API calls

# External Dependencies

## Third-Party APIs
- **ParseExtract API**: Core OCR service for extracting text from darts game screenshots
  - Requires API key and endpoint URL configuration
  - Supports additional parameters for OCR engine selection
  - Includes stub mode for development/testing without API calls

## Python Libraries
- **Flask**: Web framework for REST API and static file serving
- **Flask-CORS**: Cross-origin resource sharing support
- **Requests**: HTTP client for ParseExtract API integration
- **SQLite3**: Built-in database for local data storage
- **Werkzeug**: Flask's underlying WSGI toolkit for request handling

## Development Tools
- **Pathlib**: Modern path handling for file operations
- **JSON**: Data serialization for configuration and API responses
- **Logging**: Debug and error tracking

## Browser Requirements
- Modern web browser with JavaScript support for the web interface
- File upload API support for image submission
- Fetch API or XMLHttpRequest for AJAX calls to the backend