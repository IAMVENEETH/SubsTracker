# SubTrack

A modern Django web app to track, manage, and get reminders for all your subscriptions.

## Features
- User registration, login, and profile management
- Add, edit, delete, and renew subscriptions
- Filter subscriptions by billing cycle, status, and price range
- Import/export subscriptions as CSV
- Email reminders for upcoming renewals (user-configurable days)
- Beautiful, responsive UI with custom color palette
- Settings page with sidebar (edit profile, change password, reminder settings)

## Tech Stack
- Django 5
- Bootstrap 5
- PostgreSQL (recommended for production)
- Railway (for deployment)

## Getting Started

### 1. Clone the repo
```sh
git clone <your-repo-url>
cd <your-repo-folder>
```

### 2. Set up a virtual environment
```sh
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies
```sh
pip install -r requirements.txt
```

### 4. Set up environment variables
Create a `.env` file or set these in Railway:
- `DJANGO_SECRET_KEY` (required)
- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (for email reminders)

### 5. Run migrations and create a superuser
```sh
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 6. Run the development server
```sh
python manage.py runserver
```

## Deployment (Railway)
1. Push your code to GitHub.
2. Go to [railway.app](https://railway.app/) and create a new project from your repo.
3. Add environment variables in Railway dashboard.
4. Railway will auto-deploy your app. Visit the provided URL!

## CSV Import/Export
- **Import:** Use the "Add New" dropdown → "Import from CSV". CSV columns: `service_name,price,billing_cycle,renewal_date`
- **Export:** Use the "Export CSV" button to download all your subscriptions.

## Email Reminders
- Users can set how many days before renewal they want to receive reminders (in Settings).
- The app will send emails using your configured SMTP settings.

## Customization
- Change the color palette in `base.html` (CSS variables).
- Add more settings or features as needed!

## License
MIT 