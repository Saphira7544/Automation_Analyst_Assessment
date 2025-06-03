# logger.py

import logging

# Configure logging
logging.basicConfig(
    filename='merchant_operations.log', 
    level=logging.INFO, 
    format='[%(asctime)s] %(message)s', 
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Log information messages
def log_info(message):
    logging.info(message)

# Log error messages
def log_error(message):
    logging.error(message)
