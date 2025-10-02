# GreenFlight Optimizer

A Django web application for optimizing flight routes and calculating environmental impact using AI-powered analytics.

## Features

- **Flight Route Optimization**: Compare aircraft efficiency and find optimal routes
- **Environmental Impact Analysis**: Calculate CO₂ emissions and fuel savings
- **User Authentication**: Secure login and registration system
- **Eco Score Tracking**: Personal environmental impact dashboard
- **AI Predictions**: Machine learning-powered emissions forecasting
- **PDF Reports**: Generate sustainability reports

## Local Development

### Prerequisites
- Python 3.12+
- Git

### Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd flightcode

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## Deployment

### Render (Recommended - Most Reliable)

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Push Code to GitHub**
   ```bash
   git add .
   git commit -m "Ready for Render deployment"
   git push origin main
   ```

3. **Create PostgreSQL Database**
   - Click "New" → "PostgreSQL"
   - Name: `greenflight-db`
   - Copy the `DATABASE_URL` (you'll need this later)

4. **Create Web Service**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Name:** `greenflight-optimizer`
     - **Runtime:** `Python 3`
     - **Build Command:** `pip install -r requirements.txt && python manage.py collectstatic --noinput --clear`
     - **Start Command:** `gunicorn flightcode.wsgi:application --bind 0.0.0.0:$PORT`

5. **Environment Variables**
   In your web service → Environment:
   ```
   DJANGO_SETTINGS_MODULE=flightcode.settings
   DEBUG=False
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=postgresql://... (paste from database)
   ```

6. **Deploy**
   - Click "Create Web Service"
   - Render will build and deploy automatically

### Heroku Deployment

1. **Install Heroku CLI**
   ```bash
   # Create Heroku app
   heroku create your-app-name

   # Set environment variables
   heroku config:set SECRET_KEY=your-secret-key-here
   heroku config:set DEBUG=False
   heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com

   # Deploy
   git push heroku main

   # Run migrations
   heroku run python manage.py migrate
   ```

### Manual VPS Deployment

```bash
# Install dependencies
sudo apt update
sudo apt install python3 python3-pip postgresql nginx

# Setup PostgreSQL
sudo -u postgres createdb flightcode
sudo -u postgres createuser --interactive flightcode_user

# Configure Nginx and Gunicorn
# Copy configuration files and restart services
```

## Environment Variables

Create a `.env` file in production:

```env
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://user:password@host:port/database
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Project Structure

```
flightcode/
├── flightcode/          # Django project settings
├── optimiser/           # Main app
│   ├── models.py        # Database models
│   ├── views.py         # View functions
│   ├── templates/       # HTML templates
│   └── management/      # Custom management commands
├── accounts/            # User authentication
├── static/              # Static files (CSS, JS)
├── media/               # User uploaded files
└── requirements.txt     # Python dependencies
```

## API Endpoints

- `GET /` - Home page
- `POST /api/optimise-flight/` - Optimize flight routes
- `GET /dashboard/` - User dashboard (login required)
- `GET /analytics/` - Analytics dashboard (login required)
- `GET /api/predictive-analysis/` - AI predictions (login required)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## License

This project is licensed under the MIT License.# Deployment triggered
# Force redeploy
