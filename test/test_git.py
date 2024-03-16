import os
from pathlib import Path

import pytest
import git

REPO_URL = 'git@github.com:RincewindWizzard/mkdocs-build-webhook.git'
REPO_NAME = 'mkdocs-build-webhook.git'
GIT_DIR = Path('../dist/git_dir')


def test_clone():
    git.Repo.clone_from(REPO_URL, GIT_DIR / REPO_NAME)
