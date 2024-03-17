import json
import os
import toml
from pathlib import Path

from loguru import logger
import dotenv


def load_config():
    dotenv.load_dotenv()

    config_path = Path(os.environ.get('WEBHOOK_CONFIG')) \
        if os.environ.get('WEBHOOK_CONFIG') \
        else Path('/etc/mkdocs-build-webhook/mkdocs-build-webhook.conf')

    with open(config_path, 'r') as f:
        config = toml.load(f)

    git_dir = os.environ.get('WEBHOOK_GIT_DIR')
    if git_dir is not None:
        config['paths']['git'] = git_dir

    www_dir = os.environ.get('WEBHOOK_WWW_DIR')
    if www_dir is not None:
        config['paths']['www'] = www_dir

    secret = os.environ.get('WEBHOOK_SECRET')
    if secret is not None:
        logger.debug('loading secret from ENV')
        config['auth']['secret'] = secret

    if config['auth']['secret'] is None:
        logger.error(f'WEBHOOK_SECRET must be set!')
        raise ValueError('WEBHOOK_SECRET must be set!')

    if config['paths']['git'] is None:
        logger.error(f'GIT_DIR must be set!')
        raise ValueError('GIT_DIR must be set!')

    if config['paths']['www'] is None:
        logger.error(f'WWW_DIR must be set!')
        raise ValueError('WWW_DIR must be set!')
    return config
