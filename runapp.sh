#!/bin/bash
#Bash Script to act as an entrypoint to help us decide if we want to debug the app or run the app

SCRIPT_NAME=$(basename "$0")

function production_run() {
    gunicorn -c $APP_CONFIG $APP_MODULE
}

function determine_python_version() {
    echo "determine python vers"
}

function simple_format_msg_echo() {
   echo "$(date) ${SCRIPT_NAME} ${1}"
}

function check_debug_address() {

    temp_debug_address=${DEBUG_ADDRESS}

    if [ -z "$DEBUG_ADDRESS" ]
    then
        temp_debug_address='0.0.0.0'
    fi
    echo $temp_debug_address
}

function check_flask_port() {
    temp_flask_port=${FLASK_PORT}

    if [ -z "$FLASK_PORT" ]
    then
        temp_flask_port=8080
    fi
    echo $temp_flask_port
}

simple_format_msg_echo "Starting Entrypoint Script"

if [ ! -z "$REMOTE_DEBUG" ] && [ "$REMOTE_DEBUG" = "true" ]
then
    simple_format_msg_echo "Remote Debugging Enabled for Application Entry"
    DEBUG_ADDRESS=$(check_debug_address)
    simple_format_msg_echo "Debug Address: ${DEBUG_ADDRESS}"

    if [ -z "$DEBUG_PORT" ]
    then
        simple_format_msg_echo "Debug Port not provided"
        simple_format_msg_echo "Will run gunicorn provided option"
        production_run
    fi

    export FLASK_HOST=${DEBUG_ADDRESS}
    export FLASK_PORT=$(check_flask_port)
    simple_format_msg_echo "Flask Host: ${FLASK_HOST}"
    simple_format_msg_echo "Flask Port: ${FLASK_PORT}"
    simple_format_msg_echo "Debug Port: ${DEBUG_PORT}"
    simple_format_msg_echo "Debug Address: ${DEBUG_ADDRESS}"
    python3 ./runapp.py 
    

elif [ -n "$ODO_DEBUG" ] && [ "$ODO_DEBUG" = "true" ]
then
    simple_format_msg_echo "ODO Debugging Enabled for Application Entry"    

    if [ -z "$DEBUG_PORT" ]
    then
        simple_format_msg_echo "Debug Port not provided"
        simple_format_msg_echo "Will run gunicorn provided option"
        production_run
    else
        export FLASK_HOST=$(check_debug_address)
        export FLASK_PORT=$DEBUG_PORT
        python3 ./runapp.py
    fi
else
    simple_format_msg_echo "No Debugging Enabled for Application Entry"
    production_run
fi

