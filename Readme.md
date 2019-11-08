# Aileen

Aileen is a sensor data aggregation tool. It can be used for any numerical sensor data, is robust and privacy-friendly.

All you need to implement is the code which reads your sensor data.

Aileen provides a server to receive data from Aileen boxes. The server displays a dashboard with a map of the boxes and their collected data.

See implementation examples at https://github.com/aileenproject (counting wifi devices & LAN-connected PCs).

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

## environment vaiables

To run the aileen box you'll to at least tell it how to find the sensor code. First, you need to adapt the PYTHONPATH:

```
export PYTHONPATH=$PYTHONPATH./your/path/to/sensor-module
```

Second, you need to set the name of the python module containing the sensor module functions (see above).
For example, if the sensor module is called "sensor.py":

```
export AILEEN_SENSOR_MODULE=sensor
```

And probably you want to tell Aileen how to activate your virtual environment:

```
export AILEEN_ACTIVATE_VENV_CMD=<your command to activate the virtual environment> 
```

By the way, you can also set these environment variables (apart from PYTHONPATH!) in an `aileen/.env` file:

```
AILEEN_SENSOR_MODULE=sensor
AILEEN_ACTIVATE_VENV_CMD=<your command to activate the virtual environment> 
```


These are other env variables, which you can alter (see aileen/settings for more info), either on the shell or the .env file:

* AILEEN_SENSOR_FILE_PREFIX
* AILEEN_BOX_PORT
* AILEEN_SENSOR_LOG_INTERVAL_IN_SECONDS
* AILEEN_INTERNET_CONNECTION_AVAILABLE
* AILEEN_UPLOAD_INTERVAL_IN_SECONDS
* AILEEN_UPLOAD_MAX_NUMBER_PER_REQUEST
* AILEEN_STATUS_MONITORING_INTERVAL_IN_SECONDS
* AILEEN_PROCESS_RESTART_INTERVAL_IN_SECONDS
* AILEEN_HASH_OBSERVABLE_IDS
* AILEEN_HASH_ITERATIONS
* AILEEN_UPLOAD_EVENTS


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
