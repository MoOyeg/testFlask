#!/bin/bash -x
#Bash Script to act as an entrypoint to help us decide if we want to debug the app or run the app


function production_run() {
    gunicorn -c $APP_CONFIG $APP_MODULE
}

function determine_python_version() {
    echo "determine python vers"
}

if [ ! -z "$REMOTE_DEBUG" ]
then
    if [ "$REMOTE_DEBUG" = "true" ]
    then
        if [ -z "$DEBUG_ADDRESS" ]
        then
            DEBUG_ADDRESS='0.0.0.0'
        fi

        if [ -z "$DEBUG_PORT" ]
        then
            echo "Debug Port not provided"
            echo "Will run gunicorn provided option"
            production_run
        else
            export FLASK_HOST=0.0.0.0
            export FLASK_PORT=8080
            python3 ./runapp.py 
        fi
    else
        production_run
    fi
else
    production_run
fi

