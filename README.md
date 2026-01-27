# medilink_backend

Backend service for the Medilink application, built with Django.

## Prerequisites

- Python 3.x installed and available on your PATH
- pip installed
- (Optional but recommended) Virtual environment tool such as `venv`

## Setup

1. Clone or download this repository.
2. Open a terminal in the project root (where `manage.py` is located).
3. Create and activate a virtual environment (if you don't already have one):

	```powershell
	python -m venv venv
	.\venv\Scripts\Activate.ps1
	```

4. Install dependencies:

	```powershell
	pip install -r requirements.txt
	```

## Running the Development Server

1. Ensure the virtual environment is activated:

	```powershell
	.\venv\Scripts\Activate.ps1
	```

2. Apply database migrations:

	```powershell
	python manage.py migrate --settings=core.settings.development
	```

3. Start the Django development server:

	```powershell
	python manage.py runserver --settings=core.settings.development
	```

4. Open your browser and go to:

	```
	http://127.0.0.1:8000/
	```

## Running in Production (basic)

To run with production settings (for example, on a server), you can use:

```powershell
python manage.py migrate --settings=core.settings.production
python manage.py collectstatic --noinput --settings=core.settings.production
python manage.py runserver 0.0.0.0:8000 --settings=core.settings.production
```

Adjust host, port, and deployment method (e.g. Gunicorn, IIS, Nginx/uwsgi) as needed for your environment.
