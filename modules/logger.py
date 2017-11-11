import logging


def log():
    logging.basicConfig(filename="logs/finances.log",
                        level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger(__name__)
    # Disable logging for certain built in modules being called.
    hide('requests')
    return logger


def hide(name):
    logging.getLogger(name).setLevel(logging.WARNING)
    return
