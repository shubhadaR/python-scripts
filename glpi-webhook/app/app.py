import os
import time 
import threading
from config import app, generate_glpi_session_token

def refresh_session_token():
    global glpi_session_token
    while True:
        glpi_session_token = generate_glpi_session_token()
        # Sleep for 1 minute
        time.sleep(60)

# Start a separate thread to periodically refresh the session token
refresh_thread = threading.Thread(target=refresh_session_token)
refresh_thread.daemon = True  # The thread will exit when the main program exits
refresh_thread.start()

if __name__ == '__main__':
    ENVIRONMENT_DEBUG = os.environ.get("DEBUG", False)
    ENVIRONMENT_PORT = os.environ.get("PORT", 8080)
    ENVIRONMENT_HOST = os.environ.get("HOST", '0.0.0.0')
    app.run(host=ENVIRONMENT_HOST, port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)
    
 