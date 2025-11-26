# E-Invoice Creator

A modern web application for invoice information extraction, validation, and delivery with user authentication and management.

## Quick Start

### Starting the Application

To start the application with Docker Compose:

```bash
docker-compose up -d --build
```

After starting, access the application at:
- Frontend: http://localhost
- Backend API: http://localhost:5000

### Running Tests

**Frontend Tests (Docker):**
```bash
docker-compose --profile test run --rm frontend-test pnpm test
```

**Backend Tests (Docker):**
```bash
docker-compose exec backend pytest --cov=backend --cov-report=term-missing
```

### Creating Admin Account (Docker)

```bash
docker-compose exec backend python manage.py create-admin --email admin@example.com --password securepass123
```
### Test Invoice Files

Sample invoice files for testing are available in the `backend/example/` folder. If you need to create your own test invoices, you can use the free invoice generator at [https://www.zoho.com/us/invoice/free-invoice-generator.html](https://www.zoho.com/us/invoice/free-invoice-generator.html).
---

## Overview

E-Invoice Creator is a full-stack web application designed for Australian small and medium-sized enterprises (SMEs) to streamline invoice processing. The system extracts invoice data from PDF and image files using OCR technology, generates PEPPOL-compliant UBL 2.1 XML invoices, validates them against official standards, and enables email delivery.

### Key Features

- **User Authentication**: Secure JWT-based authentication with registration, login, and profile management
- **OCR Processing**: Automatic invoice data extraction from PDF, JPG, JPEG, and PNG files using Veryfi API
- **Invoice Creation**: Multi-step workflow for creating, editing, and managing invoices
- **XML Generation**: Automatic generation of PEPPOL UBL 2.1 compliant XML invoices
- **XML Validation**: Validation against AUNZ UBL and AUNZ PEPPOL rule sets via ESS Validator
- **Email Delivery**: Send validated XML invoices directly via email using Mailgun
- **Invoice History**: View, edit, and manage invoice records with search and filter capabilities
- **Admin Panel**: User management and system statistics (admin only)
- **Modern UI**: Clean, responsive design with dark/light theme support

## Tech Stack

### Frontend
- **Vue 3** (Composition API)
- **Element Plus** (UI Components)
- **Vue Router** (with route guards)
- **Pinia** (State Management)
- **Vite** (Build Tool)
- **Axios** (HTTP Client)
- **Jest** (Testing Framework)

### Backend
- **Flask** (Python Web Framework)
- **PostgreSQL** (Database)
- **Flask-SQLAlchemy** (ORM)
- **Flask-Migrate** (Database Migrations)
- **Flask-JWT-Extended** (JWT Authentication)
- **Flask-Bcrypt** (Password Hashing)
- **pytest** (Testing Framework)

### External Services
- **Veryfi API** (OCR Processing)
- **ESS Validator** (XML Validation)
- **Mailgun** (Email Delivery)

## Getting Started

### Prerequisites

- Docker and Docker Compose installed
- API credentials for Veryfi, ESS Validator, and Mailgun (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd demo-main
   ```

2. **Configure environment variables**
   ```bash
   cd backend
   cp env_example.txt .env
   # Edit .env and fill in your API credentials
   ```

3. **Start services with Docker Compose**
   ```bash
   cd ..
   docker-compose up -d --build
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec backend flask db upgrade
   ```

5. **Create admin user (optional)**
   ```bash
   docker-compose exec backend python manage.py create-admin --email admin@example.com --password securepass123
   ```

6. **Access the application**
   - Frontend: http://localhost
   - Backend API: http://localhost:5000

## Configuration

The application requires a `.env` file in the `backend` directory. Copy `env_example.txt` to `.env` and configure the following:

### Required Variables

```env
# Database
DATABASE_URL=postgresql://invoice_user:invoice_db_password@db:5432/invoice_db

# JWT Authentication
JWT_SECRET_KEY=your_very_long_random_secret_here
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=2592000

# Veryfi OCR API
VERYFI_CLIENT_ID=your_client_id
VERYFI_AUTHORIZATION=apikey your_username:your_api_key

# ESS Validator (Optional)
ESS_VALIDATOR_TOKEN=your_jwt_access_token_here
ESS_VALIDATOR_CLIENT_ID=your_cognito_client_id
ESS_VALIDATOR_CLIENT_SECRET=your_cognito_client_secret
ESS_VALIDATOR_TOKEN_URL=https://your-cognito-domain/oauth2/token

# Mailgun Email (Optional)
MAILGUN_DOMAIN=your_domain.mailgun.org
MAILGUN_API_KEY=your_api_key
MAILGUN_FROM_EMAIL=noreply@yourdomain.com
```

## Project Structure

```
.
├── backend/
│   ├── app.py              # Flask application entry point
│   ├── manage.py           # Management CLI commands
│   ├── models/             # Database models
│   ├── routes/             # API route blueprints
│   ├── services/           # Business logic services
│   ├── utils/              # Utility functions
│   ├── migrations/         # Database migrations
│   └── tests/              # Test suite
├── frontend/
│   ├── src/
│   │   ├── views/          # Vue page components
│   │   ├── components/     # Reusable components
│   │   ├── composables/   # Vue composables
│   │   ├── stores/         # Pinia stores
│   │   ├── router/         # Vue Router configuration
│   │   └── utils/          # Utility functions
│   └── tests/              # Frontend tests
└── docker-compose.yml      # Docker Compose configuration
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/profile` - Get current user profile
- `PUT /api/auth/profile` - Update user profile

### Invoice Management
- `GET /api/invoices` - Get user's invoice list (paginated)
- `GET /api/invoices/<id>` - Get invoice details
- `PUT /api/invoices/<id>` - Update invoice OCR data
- `DELETE /api/invoices/<id>` - Delete invoice

### OCR Processing
- `POST /api/ocr` - Upload and process invoice document
  - Supported formats: PDF, JPG, JPEG, PNG
  - Max size: 10MB

### XML Operations
- `POST /api/generate-xml` - Generate UBL XML from invoice data
- `POST /api/validate-xml` - Validate XML against PEPPOL standards
- `POST /api/upload-xml` - Upload XML file for validation

### Email
- `POST /api/send-email` - Send XML invoice via email

### Admin (Admin Only)
- `GET /api/admin/users` - Get user list (paginated)
- `PUT /api/admin/users/<id>/toggle` - Enable/disable user
- `GET /api/admin/stats` - Get system statistics

## Testing

### Test Structure

#### Backend Tests

```
backend/tests/
├── conftest.py              # Pytest configuration and shared fixtures
├── pytest.ini               # Pytest configuration file
├── unit/                    # Unit tests
│   ├── test_models.py       # Model tests
│   ├── test_auth.py         # Authentication utility tests
│   ├── test_services.py     # Service layer tests
│   └── test_utils.py        # Utility function tests
├── integration/             # Integration tests
│   ├── test_auth_api.py     # Authentication API tests
│   ├── test_invoices_api.py # Invoice API tests
│   ├── test_admin_api.py    # Admin API tests
│   ├── test_ocr_xml_api.py  # OCR/XML API tests
│   └── test_email_api.py    # Email API tests
├── fixtures/                # Test data fixtures
│   ├── users.py             # User test data
│   └── invoices.py          # Invoice test data
└── helpers/                 # Test helper functions
    └── client.py            # Flask test client utilities
```

#### Frontend Tests

```
frontend/tests/
├── setup.js                 # Jest configuration and setup
├── unit/
│   ├── composables/        # Composable tests
│   │   ├── useFileUpload.test.js
│   │   ├── useInvoiceForm.test.js
│   │   ├── useXmlOperations.test.js
│   │   └── useXmlUpload.test.js
│   ├── stores/              # Store tests
│   │   └── auth.test.js
│   └── utils/               # Utility tests
│       └── axios.test.js
```



## Usage

### For Regular Users

1. **Register/Login**: Create an account or sign in
2. **Create Invoice**: 
   - Upload a PDF/JPG/JPEG/PNG invoice document
   - Review and edit extracted information
   - Generate UBL XML format
   - Validate against PEPPOL standards
   - Send via email or download
3. **View History**: Access invoice history to view, edit, or delete past invoices

### For Administrators

1. **Admin Panel**: Access the admin dashboard from navigation
2. **User Management**: View all users, enable/disable accounts
3. **System Statistics**: View system-wide statistics

## License

MIT
