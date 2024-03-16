import hashlib
import hmac
import json
import os
import shutil
import subprocess
from pathlib import Path

import git
from flask import Flask, request, jsonify, abort

from loguru import logger

app = Flask(__name__)

WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
GIT_DIR = Path(os.environ.get('WEBHOOK_GIT_DIR'))
WWW_DIR = Path(os.environ.get('WEBHOOK_WWW_DIR'))


@app.route("/", methods=['GET'])
def index():
    return "<p>Hello, World!</p>"


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
                shutil.copytree(repo_dir / 'site', WWW_DIR / repo_name)
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
