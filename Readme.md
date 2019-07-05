# Aileen

Aileen is a sensor data aggregation tool. It can be used for any numerical sensor data, is robust and privacy-friendly.


## Dependencies

- Make a virtual environment: `virtualenv env_aileen`
- Activate it, e.g: `source env_aileen/bin/activate`
- Install the `aileen` dependencies:
  `python setup.py develop`
- If you want to collaborate on code, please install pre-commit for it to hook into commits:
  `pre-commit install`


## Sensor module

To run the aileen box you'll need a module implementing three functions:

* start_sensing(tmp_path: str)
* get_latest_reading_as_df(tmp_path: str)

In addition, you can implement these additional functions:

* check_preconditions()
* adjust_event_value(event_value: float, last_event_value: float, observations: dict, observable: Observable)


## Database for development

Use sqlite

## code

- We use black for code formatting.
- We use isort for package importing.

## .env file

To run the aileen box you'll need to have the following in an `aileen/.env` file.

```
SENSOR_MODULE=sensor
PYTHONPATH=$PYTHONPATH./your/path/to/sensor-module
BOX_PORT=<some number>
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

## Data to map on server

Go to the `/admin` url and add a location for the aileen box

## Deploy server app

When creating an app on a server be sure to tell the server to collect the static files with the following
`python manage.py collectstatic`
