#!/bin/bash

echo "Generating new ssh keypair..."
ssh-keygen -t ed25519 -f /home/user/.ssh/deploy_key -C "mkdocs-build-webhook" -N ''

echo "Please add the following public key to your repositories with read access:"
cat /home/user/.ssh/deploy_key.pub
echo


gunicorn -w 4 -b 0.0.0.0:5000 mkdocs_build_webhook.__main__:app