# Aero Bound Ventures

A modern flight booking platform with real-time flight search, booking management, and integrated payment processing.

## Tech Stack

**Frontend**
- Next.js 15 (React 19) with TypeScript
- Tailwind CSS for styling
- Zustand for state management

**Backend**
- FastAPI (Python 3.12+)
- PostgreSQL database with SQLModel ORM
- Redis for caching
- Docker Compose for containerization

**Integrations**
- Amadeus Flight API for flight search and booking
- Pesapal Payment Gateway (USD only)
- Email notifications

## Project Structure

```
├── frontend/          # Next.js web application
├── backend/           # FastAPI REST API
├── terraform/         # AWS infrastructure (S3)
├── mobile/            # (Planned) Mobile app
└── shared/            # (Planned) Shared resources
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+
- Python 3.12+

### Backend Setup

```bash
cd backend

# Copy environment variables
cp .env.example .env
# Configure: AMADEUS_API_KEY, PESAPAL_CONSUMER_KEY, etc.

# Start services (FastAPI, PostgreSQL, Redis)
docker compose up --build

# API available at http://localhost:8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local
# Set: NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Start development server
npm run dev

# App available at http://localhost:3000
```

## Key Features

- **Flight Search**: Real-time search across multiple airlines via Amadeus API
- **Booking Management**: Create and track flight bookings with PNR
- **Payment Processing**: Secure payments via Pesapal (iframe modal integration)
- **User Authentication**: JWT-based authentication with secure password hashing
- **Email Notifications**: Automated booking confirmations
- **Caching**: Redis-based caching for improved performance

## API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

### Backend (`backend/.env`)
```env
# Amadeus Flight API
AMADEUS_API_KEY=your_key
AMADEUS_API_SECRET=your_secret
AMADEUS_BASE_URL=test.api.amadeus.com

# Pesapal Payment Gateway
PESAPAL_CONSUMER_KEY=your_key
PESAPAL_CONSUMER_SECRET=your_secret
PESAPAL_BASE_URL=https://cybqa.pesapal.com/pesapalv3
PESAPAL_IPN_ID=your_ipn_id

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres

# Security
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Email
MAIL_USERNAME=your_email
MAIL_PASSWORD=your_password
MAIL_SERVER=smtp.gmail.com
```

### Frontend (`frontend/.env.local`)
```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Development

### Run Tests
```bash
cd backend
pytest
```

### Database Migrations
```bash
cd backend
alembic upgrade head
```

### Code Quality
```bash
cd backend
pre-commit run --all-files
```

## Deployment

Infrastructure provisioning via Terraform (AWS S3 configured).

## License

MIT 