'''App Entrypoint For Gunicorn'''
import os
from app import create_app, db
from debugger import initialize_debugger

app = create_app()

@app.shell_context_processor

def make_shell_context():
    '''Function to set variable before app start'''
    return {'db': db }

if __name__ == '__main__':
    if os.environ.get('REMOTE_DEBUG') == "true":
        print("Debugging Enabled")
        debug_port=int(os.environ.get('DEBUG_PORT')) 
        debug_host=os.environ.get('DEBUG_ADDRESS')
        flask_port=os.environ.get('FLASK_PORT')
        flask_host=os.environ.get('FLASK_HOST')
        initialize_debugger(debug_port=debug_port,debug_host=debug_host)
        app.run(host=flask_host, port=flask_port)
    else:
        app.run()
