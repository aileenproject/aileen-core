# Aileen

{Description}

## Dependencies

* Make a virtual environment: `virtualenv env_aileen`
* Activate it, e.g: `source env/bin/activate`
* Install the `aileen` dependencies:
  `pip install -r requirements.txt`

## Database for development
Use sqlite

## .env file
To run the aileen box you'll need to have the following in a `aileen/.env` file.
```
WIFI_INTERFACES='theWifiInterfaceOfDevice'
SUDO_PWD='password'
DISABLE_AUTO_TITLE='true'
```

## First migrations and superuser
Initialize the database

  * `python manage.py makemigrations`
  * `python manage.py migrate`


Create a super user
  * `python manage.py createsuperuser`

## Test app
Check if everything was installed correctly:

`python manage.py runserver`

or

`python manage.py run_box`

## Data to Map
Go to the `/admin` url and add a location for the aileen box

## Deploy app
When creating an app on a server be sure to tell the server to collect the static files with the following
python manage.py collectstatic
