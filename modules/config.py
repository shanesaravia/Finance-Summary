import yaml


def load(filename='./configs/config.yml'):
    """ Loads config file. """
    with open(filename, 'r') as config:
        return yaml.load(config)
