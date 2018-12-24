# Aileen

Aileen, a hardware/software suite designed for NGOs, counts signals from devices with a wireless interface enabled (such as smartphones) to deliver population data in an organized and actionable format.

## Hardware

- ALFA AWUS036NH HIGH POWER WIFI USB-ADAPTER
- Computer running Ubuntu 18.04 LTS

## Dependencies

- Make a virtual environment: `virtualenv env_aileen`
- Activate it, e.g: `source env_aileen/bin/activate`
- Install the `aileen` dependencies:
  `python setup.py develop`
- If you want to collaborate on code, please install pre-commit for it to hook into commits:
  `pre-commit install`

## Database for development

Use sqlite

## code

We use black
We use isort for package importing

## .env file

To run the aileen box you'll need to have the following in an `aileen/.env` file.

```
WIFI_INTERFACES='theWifiInterfaceOfDevice'
SUDO_PWD='password'
DISABLE_AUTO_TITLE='true'
```

## First migrations and superuser

Initialize the database

- `python manage.py makemigrations`
- `python manage.py migrate`

Create a super user

- `python manage.py createsuperuser`

## Test app

Check if everything was installed correctly with either:

- `python manage.py runserver`
- `python manage.py run_box`

## Data to Map

Go to the `/admin` url and add a location for the aileen box

## Deploy app

When creating an app on a server be sure to tell the server to collect the static files with the following
`python manage.py collectstatic`
