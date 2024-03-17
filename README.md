# mkdocs-build-webhook

A webhook that builds your mkdocs projects.

Run it with

## Installation

    mkdir -p /var/share/mkdocs-build-webhook/ /var/www/ /etc/mkdocs-build-webhook/ /var/www/.ssh/
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

Install pipx:

    apt install pipx
    su www-data -s /bin/bash
    pipx install mkdocs-build-webhook

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

Activate with:

    sudo systemctl daemon-reload
    sudo systemctl enable mkdocs-build-webhook.service
    sudo systemctl start mkdocs-build-webhook.service

Does it work?

    sudo journalctl -u mkdocs-build-webhook.service -f

# Docker

    podman build -t mkdocs-build-webhook .    
    podman run  --userns keep-id --rm --name mkdocs-build-webhook -v ./dist/www/:/var/www/:z -e WEBHOOK_SECRET=secret -p 5000:5000 localhost/mkdocs-build-webhook

# Nginx and oauth2-proxy

    server {
      server_name bootsbuch.magierdinge.de;
    
    
      # OAuth 2.0 Token Introspection configuration
      #resolver 8.8.8.8;                  # For DNS lookup of OAuth server
      subrequest_output_buffer_size 16k; # To fit a complete response from OAuth server
      #error_log /var/log/nginx/error.log debug; # Enable to see introspection details
    
    
      root /var/www/bootsbuch/;
    
      proxy_http_version  1.1;
      proxy_cache_bypass  $http_upgrade;
      proxy_set_header Upgrade $http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_set_header X-Forwarded-Host $host;
      proxy_set_header X-Forwarded-Port $server_port;
      proxy_buffer_size 128k; 
      proxy_buffers 4 256k;
    
      location  ~ ^/.webhook(.*)$ {
        proxy_pass http://127.0.0.1:5000$1;
      }
        
      location = /robots.txt {
        add_header  Content-Type  text/plain;
        return 200 "User-agent: *\nDisallow: /\n";
      }
    
      # oauth2-proxy
      location / {
        proxy_pass http://127.0.0.1:4180;
        #proxy_set_header Host bootsbuch.local;
          #proxy_pass http://bootsbuch.local;
      }
    
      listen 443 ssl; # managed by Certbot
      ssl_certificate /etc/letsencrypt/live/bootsbuch.magierdinge.de/fullchain.pem; # managed by Certbot
      ssl_certificate_key /etc/letsencrypt/live/bootsbuch.magierdinge.de/privkey.pem; # managed by Certbot
      include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
      ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
    }
    server {
        #if ($host = bootsbuch.magierdinge.de) {
        #    return 301 https://$host$request_uri;
        #} # managed by Certbot
    
    
        
        server_name bootsbuch.magierdinge.de;
        listen 80;
        return 404; # managed by Certbot
    }
    
    server {
      server_name bootsbuch.local;
      root /var/www/bootsbuch/;
      location / {
        try_files $uri $uri/ =404;
      }
    }

/etc/systemd/system/oauth2-proxy.service:

    [Unit]
    Description=oauth2-proxy for microsoft login
    After=network.target
    
    [Service]
    Type=simple
    ExecStart=oauth2-proxy --config=/etc/oauth2-proxy/oauth2-proxy.conf '--email-domain=mitglied.segelgruppe-kiel.de' --upstream="http://bootsbuch.local/" --pass-host-header=false
    User=www-data
    Group=www-data
    Restart=always
    RestartSec=3
    
    [Install]
    WantedBy=multi-user.target