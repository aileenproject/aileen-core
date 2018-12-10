# Aileen

{Description}

## Dependencies

* Make a virtual environment: `virtualenv env`
* Activate it, e.g: `source env/bin/activate`
* Install the `aileen` dependencies:
  `pip install -r requirements.txt`

## Database for development
Use sqlite

## custom .zshrc
Be sure to set `DISABLE_AUTO_TITLE=true` or tmux won't be able to rename the windows

## First migrations and superuser
Initialize the database
  * `python manage.py makemigrations`
  * `python manage.py migrate`
  * `python manage.py createsuperuser`

## Create superuser
python manage.py createsuperuser

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

