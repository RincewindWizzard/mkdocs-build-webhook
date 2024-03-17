# mkdocs-build-webhook

A webhook that builds your mkdocs projects.

Run it with

## Installation

    mkdir /var/share/mkdocs-build-webhook/ /var/www/ /etc/mkdocs-build-webhook/ /var/www/.ssh/
    ssh-keyscan github.com >> /var/www/.ssh/known_hosts
    ssh-keygen -t ed25519 -f /var/www/.ssh/deploy_key -C "mkdocs-build-webhook" -N ''
    chown -R www-data:www-data /var/share/mkdocs-build-webhook/ /var/www/

Add this config to /etc/mkdocs-build-webhook/mkdocs-build-webhook.conf:

    [paths]
    git = "/var/share/mkdocs-build-webhook/"
    www = "/var/www/"
    
    [auth]
    secret = "<secret>"
    
    [gunicorn]
    bind = "0.0.0.0:5000"
    workers = 4

/var/www/.ssh/config:

    Host github.com
     HostName github.com
     Port 22
     User git
     CheckHostIP no
     IdentityFile "~/.ssh/deploy_key"

/etc/systemd/system/mkdocs-build-webhook.service:

    [Unit]
    Description=mkdocs-build-webhook Service
    After=network.target
    
    [Service]
    Type=simple
    ExecStart=/var/www/.local/pipx/venvs/mkdocs-build-webhook/bin/mkdocs-build-webhook
    User=www-data
    Group=www-data
    Restart=always
    RestartSec=3
    
    [Install]
    WantedBy=multi-user.target

# Docker

    podman build -t mkdocs-build-webhook .    
    podman run  --userns keep-id --rm --name mkdocs-build-webhook -v ./dist/www/:/var/www/:z -e WEBHOOK_SECRET=secret -p 5000:5000 localhost/mkdocs-build-webhook