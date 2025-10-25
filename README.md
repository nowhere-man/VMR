# VQMR - Video Quality Metrics Report

Web application for video encoding quality analysis using FFmpeg metrics (PSNR, VMAF, SSIM).

## Features

- **Multiple Quality Metrics**: Supports PSNR, VMAF, SSIM with Y/U/V component breakdowns
- **Visual Reports**: Frame-level quality charts using Chart.js
- **Flexible Modes**:
  - Single-file mode: Upload one video, system applies preset encoding
  - Dual-file mode: Upload reference and distorted videos for comparison
- **RESTful API**: JSON endpoints for programmatic access
- **Server-Side Rendering**: Jinja2 templates with Tailwind CSS

## Requirements

- Python 3.10+
- FFmpeg with libvmaf support
- VMAF model file (default: `/usr/share/model/vmaf_v0.6.1.json`)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/VQMR.git
cd VQMR
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env to customize settings
```

## Configuration

Configuration is managed via environment variables (see `.env.example`):

- `HOST`: Server host (default: 0.0.0.0)
- `PORT`: Server port (default: 8080)
- `JOBS_ROOT_DIR`: Task storage directory (default: ./jobs)
- `FFMPEG_TIMEOUT`: FFmpeg execution timeout in seconds (default: 600)
- `VMAF_MODEL_PATH`: Path to VMAF model file
- `RETENTION_DAYS`: Job retention period (default: 7)
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FORMAT`: Log format, json or text (default: json)

## Usage

### Quick Start

The easiest way to run the application:

```bash
./start.sh
```

### Development Mode

Run the application with auto-reload:

```bash
./venv/bin/uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8080
```

Or using Python directly:

```bash
./venv/bin/python -m backend.src.main
```

### Production Mode

```bash
./venv/bin/uvicorn backend.src.main:app --host 0.0.0.0 --port 8080 --workers 4
```

### Access the Application

- Web Interface: http://localhost:8080
- API Documentation: http://localhost:8080/api/docs
- Health Check: http://localhost:8080/health

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend/src --cov-report=html

# Run specific test types
pytest -m unit        # Unit tests only
pytest -m integration # Integration tests only
pytest -m contract    # Contract tests only

# Run tests for specific user story
pytest -m US1         # User Story 1 tests
```

## Project Structure

```
VQMR/
├── backend/
│   ├── src/
│   │   ├── api/          # API endpoints
│   │   ├── models.py     # Data models
│   │   ├── services/     # Business logic
│   │   ├── templates/    # Jinja2 templates
│   │   ├── utils/        # Utility functions
│   │   ├── config.py     # Configuration
│   │   └── main.py       # Application entry point
│   └── tests/
│       ├── contract/     # API contract tests
│       ├── integration/  # Integration tests
│       └── unit/         # Unit tests
├── frontend/
│   └── static/
│       ├── js/           # JavaScript files
│       └── css/          # CSS files
├── jobs/                 # Task storage (auto-created)
├── docs/                 # Documentation
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project configuration
└── README.md
```

## API Overview

### Create Job
```bash
POST /api/jobs
Content-Type: multipart/form-data

# Single-file mode
{
  "mode": "single_file",
  "file": <video_file>,
  "preset": "medium"
}

# Dual-file mode
{
  "mode": "dual_file",
  "reference": <reference_video>,
  "distorted": <distorted_video>
}
```

### Get Job Status
```bash
GET /api/jobs/{job_id}
```

### List Jobs
```bash
GET /api/jobs?status=completed&limit=10
```

### Get Metrics Report
```bash
GET /api/jobs/{job_id}/metrics
```

## Development

### Code Quality

```bash
# Format code
black backend/

# Type checking
mypy backend/src

# Linting
flake8 backend/
```

### Adding New Features

1. Create feature branch from main
2. Follow test-first development approach
3. Ensure test coverage >= 80%
4. Run all tests before committing
5. Create pull request for review

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please follow the project's code style and testing requirements.

## Support

For issues and questions, please open an issue on GitHub.
