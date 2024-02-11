'''App Entrypoint For Gunicorn'''
import os
from app import create_app, db
from debugger import initialize_debugger
from logging import getLogger,basicConfig,DEBUG,getLogger,StreamHandler
from sys import stdout

app = create_app()

    
@app.shell_context_processor

def make_shell_context():
    '''Function to set variable before app start'''
    return {'db': db }

if __name__ == '__main__':
    if not getLogger().hasHandlers():
        stdout_handler = StreamHandler(stream=stdout)
        handlers = [stdout_handler]
        basicConfig(
            level=DEBUG, 
            format='%(asctime)s loglevel=%(levelname)-6s logger=%(name)s %(funcName)s() L%(lineno)-4d %(message)s',
            handlers=handlers
        )
        logger = getLogger('runapp.py')
        
    if os.environ.get('REMOTE_DEBUG') == "true":
        start_debug=True
        try:
            logger.info("Debugging Enabled")
            debug_port=int(os.environ.get('DEBUG_PORT')) 
            debug_host=os.environ.get('DEBUG_ADDRESS')
            flask_port=os.environ.get('FLASK_PORT')
            flask_host=os.environ.get('FLASK_HOST')
            logger.info("Initializing Remote Debugger")
            initialize_debugger(debug_port=debug_port,debug_host=debug_host)
        except Exception as e:
            logger.error("Error in Remote Debugging: {}".format(e))
            start_debug=False
            
        if start_debug:
            logger.info("Running Flask App with Remote Debugging")
            try:
                app.run(host=flask_host, port=flask_port,debug=True, use_debugger=False, use_reloader=False)
            except OSError as error:
                if "Address already in use" in str(error):
                    logger.error("Port {} is already in use".format(flask_port))
                else:
                    logger.error("Error in Running Flask App: {}".format(error))
    elif os.environ.get('ODO_DEBUG') == "true":
        logger.info("ODO Debugging Enabled")
        flask_port=os.environ.get('FLASK_PORT')
        flask_host=os.environ.get('FLASK_HOST')
        try:
            app.run(host=flask_host, port=flask_port,debug=True, use_debugger=False, use_reloader=False)
        except OSError as error:
            if "Address already in use" in str(error):
                logger.error("Port {} is already in use".format(flask_port))
            else:
                logger.error("Error in Running Flask App: {}".format(error))
    else:
        logger.info("Debugging Disabled")
        app.run()
