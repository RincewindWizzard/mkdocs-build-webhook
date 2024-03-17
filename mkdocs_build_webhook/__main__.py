import hashlib
import hmac

import shutil
import subprocess
from pathlib import Path

import git

from flask import Flask, request, jsonify, abort

from loguru import logger

from mkdocs_build_webhook import config

app = Flask(__name__)

CONFIG = config.load_config()
GIT_DIR = Path(CONFIG['paths']['git'])
WWW_DIR = Path(CONFIG['paths']['www'])
WEBHOOK_SECRET = CONFIG['auth']['secret']

logger.debug(f'secret: {WEBHOOK_SECRET}')


@app.route("/", methods=['GET'])
def index():
    return jsonify({'msg': 'it works'}), 200


@app.route("/", methods=['POST'])
def post():
    if request.method == 'POST':
        if is_signature_ok(request.data, request.headers.get('X-Hub-Signature-256')):
            data = request.get_json()
            repo_name = data['repository']['name']
            repo_dir = GIT_DIR / repo_name
            repo_url = data['repository']['ssh_url']

            if not repo_dir.is_dir():
                logger.debug(f'Cloning {repo_url} into {repo_dir}')
                git.Repo.clone_from(repo_url, repo_dir)
            else:
                repo = git.Repo(repo_dir)
                logger.debug(f'Pulling {repo_name}')
                repo.remotes.origin.pull()

            built_successful = build_project(repo_dir)
            if built_successful:
                deploy_dir = WWW_DIR / repo_name
                if deploy_dir.is_dir():
                    shutil.rmtree(deploy_dir)
                shutil.copytree(repo_dir / 'site', deploy_dir)
                logger.debug(f'Successfully deployed {repo_name}')
                return jsonify({'msg': 'build successful'}), 200
            else:
                return jsonify({'msg': 'build failed'}), 500
        else:
            logger.debug(f'Invalid signature!')
            return jsonify({'msg': 'Invalid signature'}), 401
    return jsonify({'msg': 'Unknown error'}), 400


def build_project(project_dir: Path):
    try:
        subprocess.run(
            ['mkdocs', 'build'],
            check=True,
            cwd=project_dir
        )
        logger.debug(f'Successfully built docs for {project_dir}')
        return True
    except subprocess.CalledProcessError as e:
        logger.error("Error occurred while building documentation:", e)
        return False


def is_signature_ok(data, signature):
    if not signature:
        abort(400, 'X-Hub-Signature-256 header not found')

    expected_signature = hmac.new(WEBHOOK_SECRET.encode(), data, hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature.replace('sha256=', ''), expected_signature)


def is_main_branch(webhook_data):
    return webhook_data['ref'] == 'refs/heads/main'


def main():
    from gunicorn.app.wsgiapp import WSGIApplication

    class StandaloneApplication(WSGIApplication):
        def __init__(self, app_uri, options=None):
            self.options = options or {}
            self.app_uri = app_uri
            super().__init__()

        def load_config(self):
            config = {
                key: value
                for key, value in self.options.items()
                if key in self.cfg.settings and value is not None
            }
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

    StandaloneApplication('mkdocs_build_webhook.__main__:app', CONFIG['gunicorn']).run()


if __name__ == '__main__':
    main()
