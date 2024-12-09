Etherport
=========

![](http://osp.kitchen/api/osp.tools.ethertoff/raw/iceberg/ethertoff-write-read-print.gif)

Etherport functions as an open-source, free-to-use tool developed especially for cultural organizations. Etherport is based on the tool patchwork Ethertoff, a simple collaborative
web platform, much resembling a wiki but featuring realtime editing thanks to Etherpad.
Its output is constructed with equal love for print and web.

> Just a question: I thought it was ethertopff and not ethertoff but I don't
> remember why. What is the actual name?
>
> Well someone misspelled ethertopdf as ethertopf which sounds like römertopf
> and than somebody else understood ethertoff like chokotoff and chokotoff
> being Bruxellois I thought it might be the best of all these references


Ethertoff has been initially developed for the OSP 2013 Summerschool bearing the name ‘Relearn’.

<http://relearn.be/>

Ethertoff is structured as a wiki where each page constitutes an Etherpad.

The pad is available to logged in users (‘write-mode’).
The text of the pad is available to everyone (‘read-mode’).

Ethertoff is a shell for an Etherpad installation hosted on the same domain.
This integration is based on Sofian Benaissa’s bridge between Django and Etherpad,
originally created for THINK WE MUST/CON-VOCATION a performance during Promiscuous
Infrastructures entrelacées, an exhibition by the collective Artivistic at SKOL.

-  <https://github.com/sfyn/django-etherpad-lite>
-  <http://www.riotnrrd.info/tech/etherpad-lite-performances-ongoing-saga>
-  <http://www.thinkwemust.org/?page_id=6>

- - -

## Installation instructions

Ethertoff is a python application using the Django framework. It needs to be
able to connect to an instance of etherpad-lite. These instructions assume the
etherpad-lite will be installed on the same server.

These instructions will install ethertoff  python application you'll need a wsgi-server (gunicorn). Normally you do not expose this to the internet but place nginx in between, also it is advised to let nginx serve the static & media files. The gunicorn.sh starts the server.

To make it easy to start and stop the application it is deployed as a systemd
service.
for this you need a service unit file. The file describes how the service should be started and when. In this case it starts the gunicorn.sh script with the correct user & group.

## Installing ethertoff on a server

### Assumptions

This installation guide makes a few assumptions.

- It will be installed on a linux distribution
- System username and group of ethertoff will be ethertoff
- Ethertoff will be installed in /srv/ethertoff
- Ethertoff will have a virtual environment in /srv/ethertoff/venv
- Etherpad will be installed in /srv/etherpad 

- nginx will be used as reverse proxy
- MariaDB will be used as the database

Both etherport and etherpad need a database. Both support various databases (sqlite, MariaDB, postgre, ...). Etherpad advices against using sqlite. Given the few write operations etherport does sqlite would not be a real problem. But. If you install a more performant database you can use it for etherport too.

### Installing depencies

```bash
sudo apt install nginx ufw fail2ban mariadb-server build-essential libmariadb-dev-compat libmariadb-dev libpython3-dev git virtualenv certbot python3-certbot-nginx nodejs npm
```


### Cloning the repository, installing dependencies

The bash script below will create a user (and group) `ethertoff`,clone the repository and install dependencies.

```bash
SYS_USER_ETHERTOFF='ethertoff'              # Username of created group
SYS_LOCATION_ETHERTOFF='/srv/ethertoff'     # Installation location of ethertoff

GIT_URL_ETHERTOFF='https://gitlab.constantvzw.org/osp/tools.ethertoff.git'
GIT_BRANCH_ETHERTOFF='going-hybrid'

# Create ethertoff user and add a folder
sudo adduser --system --home $SYS_LOCATION_ETHERTOFF --group $SYS_USER_ETHERTOFF

# Move to created folder
cd $SYS_LOCATION_ETHERTOFF

# Copy local_settings.py.example to local_settings.py
sudo -u $SYS_USER_ETHERTOFF cp tools.ethertoff/my_project/local_settings.py.example tools.ethertoff/my_project/local_settings.py

# Clone repo
sudo -u $SYS_USER_ETHERTOFF git clone -b $GIT_BRANCH_ETHERTOFF --depth 1 $GIT_URL_ETHERTOFF

# Create a virtual environment and install dependencies
sudo -u $SYS_USER_ETHERTOFF virtualenv -p python3 venv
sudo -u $SYS_USER_ETHERTOFF venv/bin/pip install -r tools.ethertoff/requirements.txt
sudo -u $SYS_USER_ETHERTOFF venv/bin/pip install gunicorn

sudo -u $SYS_USER_ETHERTOFF mkdir logs
```

### Database tables

The following commands create a user and table for ethertoff, identified by the defined password.

```bash
DB_NAME_ETHERTOFF='django'
DB_USER_ETHERTOFF='django'
DB_PASSWORD_DJANGO='change_the_password'

SQL_DJANGO="CREATE DATABASE ${DB_NAME_ETHERTOFF}; CREATE USER '${DB_USER_ETHERTOFF}'@'localhost' IDENTIFIED BY '${DB_PASSWORD_DJANGO}'; GRANT ALL on ${DB_NAME_ETHERTOFF}.* TO '${DB_USER_ETHERTOFF}'@'localhost';"
echo $SQL_DJANGO > /tmp/sql_django;
sudo mariadb < /tmp/sql_django;
rm /tmp/sql_django
```

The credentials should be added to the etherport configuration so django can connect to the database. Edit `/srv/ethertoff/tools.ethertoff/my_project/local_settings.py` and make sure the database configuration has the correct credentials. Normally it's a matter of setting the password.

Make sure the database settings are correct:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', 'NAME': 'django',
        'USER': 'django',
        'PASSWORD': 'change_the_password',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost th>
        'PORT': '',                      # Set to empty string for default.
    }
}
```

*tip:* as the files are owned by the user `ethertoff` it's easiest to edit the files as that user. So:

```bash
sudo -u etherpad nano /srv/ethertoff/tools.ethertoff/my_project/local_settings.py
```

## 

Now that ethertoff has been configured it is time to set the database structure using:

```bash
sudo -u ethertoff /srv/ethertoff/tools.ethertoff/manage.py migrate
```

Finally set an admin user, or superuser:

```bash
sudo -u ethertoff /srv/ethertoff/tools.ethertoff/manage.py createsuperuser
```


## Configuring gunicorn

Use gunicorn as WSGI-server. This configureation tells gunicorn where to find the code, how much processes to spwan, logs, etc...

Place in `/srv/ethertoff/gunicorn.sh`

```bash
#! /usr/bin/env bash

NAME="ethertoff"                                       # Name of the application
USER=ethertoff                                         # the user to run as
GROUP=ethertoff                                        # the group to run as
DJANGODIR=/srv/ethertoff/tools.ethertoff               # Django project directory
SOCKFILE=/tmp/gunicorn-ethertoff.sock                  # we will communicte using this unix socket
NUM_WORKERS=3                                          # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=my_project.settings     # which settings file should Django use
DJANGO_WSGI_MODULE=my_project.wsgi             # WSGI module name
LOG_FILE=/srv/ethertoff/logs/gunicorn                  # Log file
VENV=/srv/ethertoff/venv/                              # Location of the virtual environment

cd $DJANGODIR

echo "Starting $NAME as `whoami`"

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn

exec $VENV/bin/gunicorn ${DJANGO_WSGI_MODULE} \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=debug \
  --log-file=$LOG_FILE
```


# Unit file

Place in `/etc/systemd/system/ethertoff.service`

```
[Unit]
Description=Ethertoff, wrapper around etherpad
After=syslog.target network.target

[Service]
Type=simple
User=ethertoff
Group=ethertoff
Restart=on-failure
WorkingDirectory=/srv/ethertoff/
ExecStart=/srv/ethertoff/gunicorn.sh

[Install]
WantedBy=multi-user.target
```

Then enable the service with:

```
sudo systemctl enable ethertoff.service
```

To start ethertoff:
```
sudo service ethertoff start
```

To check whether ethertoff is running:
```
sudo service ethertoff status
```

An expected output would look like:
```
   Main PID: 194687 (gunicorn)
      Tasks: 4 (limit: 2296)
     Memory: 270.8M
        CPU: 17min 49.565s
     CGroup: /system.slice/ethertoff.service
             ├─1994987 /srv/ethertoff/venv/bin/python /srv/ethertoff/venv/...
             ├─1994990 /srv/ethertoff/venv/bin/python /srv/ethertoff/venv/...
             ├─1994991 /srv/ethertoff/venv/bin/python /srv/ethertoff/venv/...
             └─1994992 /srv/ethertoff/venv/bin/python /srv/ethertoff/venv/...

```

If ever you want to stop ethertoff:
```
sudo service ethertoff stop
```


### Reverse proxy

It is generally advised to not make the WSGI-server publicly accesible, but to place it behind a reverse proxy. In this case nginx.

NGINX config file. 

```nginx
# https://nginx.org/en/docs/http/websocket.html
# Upgrade connections to allow for websockets
# should improve etherpad performance
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

# Forward to socket managed by gunicorn
upstream ethertoff {
    # for UNIX domain socket setups
    server unix:/tmp/gunicorn-ethertoff.sock fail_timeout=0;
}

# Forward to etherpad on its default port.
# Remove when there is no etherpad installed
upstream etherpad {
    server localhost:9001 fail_timeout=0;
}

server {
    server_name default_server;
    
    access_log  /var/log/nginx/access.log;
    error_log  /var/log/nginx/error.log;
    client_max_body_size 500m;

    location /publications/ {
        alias /srv/ethertoff/static/generator/generated/;
    }

    location /media/ {
        alias /srv/ethertoff/media/;
    }

    location  /static/ {
        alias /srv/ethertoff/static/;
        autoindex  off;
    }

    # Forward traffic to etherpad
    location /ether/ {
        rewrite                /ether/(.*) /$1 break;
        proxy_pass             http://etherpad;
        proxy_redirect         / /ether/;
        proxy_set_header       Host $host;
        proxy_buffering off;

        # Allow websockets
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
    }

    # Specific to etherport
    location = / {
        return 302 https://etherport.org/publications/;
    }

    # This is the Ethertoff instance: a django app, which wraps around
    # The Etherpad install
    location / {
        proxy_pass http://ethertoff;
        proxy_set_header Host $http_host;
        proxy_redirect off;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        add_header 'Access-Control-Allow-Origin' '*';
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS';
    }
}
```



## Etherpad


### Create system user

```bash
SYS_USER_ETHERPAD='etherpad'
SYS_LOCATION_ETHERPAD='/srv/etherpad'
# Create etherpad user and folder
sudo adduser --system --home $SYS_LOCATION_ETHERPAD --group $SYS_USER_ETHERPAD
cd $SYS_LOCATION_ETHERPAD
```

### Clone etherpad

```bash
GIT_URL_ETHERPAD='https://github.com/ether/etherpad-lite.git'
GIT_BRANCH_ETHERPAD='master'
sudo -u $SYS_USER_ETHERPAD git clone -b $GIT_BRANCH_ETHERPAD --depth 1 $GIT_URL_ETHERPAD
```


### DB Structure

```bash
DB_NAME_ETHERPAD='etherpad'
DB_USER_ETHERPAD='etherpad'
DB_PASSWORD_ETHERPAD='change_this_password'
# SQL SETUP
SQL_ETHERPAD="CREATE DATABASE ${DB_NAME_ETHERPAD}; CREATE USER '${DB_USER_ETHERPAD}'@'localhost' IDENTIFIED BY '${DB_PASSWORD_ETHERPAD}'; GRANT ALL on ${DB_NAME_ETHERPAD}.* TO '${DB_USER_ETHERPAD}'@'localhost';"
echo $SQL_ETHERPAD > /tmp/sql_etherpad
sudo mariadb < /tmp/sql_etherpad
rm /tmp/sql_etherpad
```


### Set etherpad configuration
`/srv/etherpad/etherpad-lite/settings.json`

Consult the etherpad documentation for settings. But at least set the DB config (disable the default dirty db configuration and enable the MySQL / MariaDB one):



```json
  "dbType" : "mysql",
  "dbSettings" : {
    "user":     "etherpad",
    "host":     "localhost",
    "port":     3306,
    "password": "change_this_password",
    "database": "etherpad",
    "charset":  "utf8mb4"
  },
```

*tip:* as the files are owned by the user `etherpad` it's easiest to edit the files as that user. So:

```bash
sudo -u etherpad nano /srv/etherpad/etherpad-lite/settings.json
```

### Set API Key

Set the API-key by changing `/srv/etherpad/etherpad-lite/APIKEY.txt`.

### Test run

```bash
sudo -u etherpad /srv/etherpad/etherpad-lite/run.sh
```

### Unit file

If etherpad is running well. You can enable it as a service through a unit file. Save as `/etc/systemd/system/etherpad.service.

```
[Unit]
Description=Etherpad-lite, the collaborative editor.
After=syslog.target network.target

[Service]
Type=simple
User=etherpad
Group=etherpad
WorkingDirectory=/srv/etherpad/etherpad-lite
Environment=NODE_ENV=production
ExecStart=/srv/etherpad/etherpad-lite/bin/run.sh
Restart=always # use mysql plus a complete settings.json to avoid Service hold-off time over, scheduling restart.

[Install]
WantedBy=multi-user.target
```

To enable the service:

```bash
sudo systemctl enable etherpad.service
```

Finally, start it:

```
sudo service etherpad start
```


### If you have the error "Site matching query does not exist"

Open the python shell

    python manage.py shell

And then do the following (replace the "domain" and "name" with your own info):

    from django.contrib.sites.models import Site
    site = Site.objects.create(domain='example.com', name='example.com')
    site.save()
    


## Install Etherpad-lite
    
    mkdir -p ~/src
    cd ~/src
    git clone https://github.com/ether/etherpad-lite.git
    
## --> install node js
Install Make:

    sudo aptitude install build-essentials

Linux Binaries (.tar.gz) from http://nodejs.org/download/



## Launch Etherpad-lite

run Etherpad with:
    
    ~/src/etherpad-lite/bin/run.sh
    
Your Etherpad is running at http://127.0.0.1:9001/
    
In Etherpad’s folder, you will find a file called APIKEY.txt
you need its contents later 



## Launch Ethertoff

Run the server:
    python manage.py runserverh

visit the admin at: http://127.0.0.1:800/admin/
you can login with the superuser you created when you synced the database
Now, on the Django admin:

    Etherpadlite > Servers > Add
        # if local
        url: http://127.0.0.1:9001/
        # if on a server
        url: http://domainname/ether/
        api_key: the contents of the file APIKEY.txt in Etherpad files

Go back to the admin home, and then add a new group:
    Auth > Groups > Add
    
Go back to the admin home, and then add the superuser (and all needed users) to the group you just created
    Auth > Users

Go back to the admin home, and then create an Etherpad Group based upon the group and the server you just created.
    Etherpadlite > Groups > Add
    
Now Ethertoff is served at http://127.0.0.1:8000/ locally, or on your domain name on a server.

You can set the site name, that appears on the header, in the ‘sites’ app in the admin.

- - -

[^1]: Something like:

    mkdir -p ~/venvs/
    cd ~/venvs/
    virtualenv ethertoff
    source ~/venvs/ethertoff/bin/activate

- - -

# Extra challenge! Installing on a server.

Some extra challenges. Basically we can split it up like:

example.com /        -> django
            /ether/  -> etherpad
            /static/ -> django static files

To test if everything is working, you can use screen to run gunicorn and Etherpad scripts at the same time, and then use a daemon like Supervisor to run them in the background.



## MYSQL

    # pip install "distribute>0.6.24"
    sudo aptitude install libmysqlclient-dev python-dev
    pip install MySQL-python mysqlclient


## DJANGO
The django application runs through mod_wsgi (Apache) or gunicorn
(nginx), or whatever way you prefer to run your wsgi python apps.
You map it to the root of your domain.

For django, we need to set up some folder where the static files
are collected. You do this with the command: `python manage.py collectstatic`
This folder we then serve through nginx or apache, and map to the
folder /static/.

    sudo aptitude install nginx
    pip install gunicorn
    cd /etc/nginx/sites-available/
    # (edit nginx config file)
    sudo vim ethertoff.conf
    cd ../sites-enabled/
    sudo ln -s ../sites-available/ethertoff
    cd ethertoff_directory/
    # (edit gunicorn config file)
    vim run.sh 
    chmod +x run.sh
    sudo service nginx start
    # Run the server
    ./run.sh

To run the server in the background, use Supervisor daemon.



## ETHERPAD
Etherpad, finally, runs as its own server. You probably need to use
a supervisor such as supervisord to make sure it keeps running.
You will also need to set up a database, because its default database
is not intended for use on servers. Finally, you will need to reverse
proxy the Etherpad process from your main web server, mapping it to
a folder such as /ether/.



## SUPERVISOR
To run django and etherpad in the background.

    sudo aptitude install supervisor
    # Edit specific config file for each application in /etc/supervisor/conf.d/
    # Example of config file:

    [program:pads]
    directory = /absolute/path/to/etherpad-lite/bin/
    user = username
    command = /absolute/path/to/etherpad-lite/bin/run.sh
    stopwaitsecs=60

    stdout_logfile = /absolute/path/to/etherpad-lite/logfile.log
    stderr_logfile = /absolute/path/to/etherpad-lite/logfile.log

    # Then run the apps daemon
    supervisord
    supervisorctl start app_name

## Systemd service
```
[Unit]
Description=Ethertoff
After=syslog.target network.target

[Service]
Type=simple
User=ethertoff
Group=ethertoff
Restart=on-failure
WorkingDirectory=/srv/ethertoff/
ExecStart=/srv/ethertoff/gunicorn.sh

[Install]
WantedBy=multi-user.target
```

## Update on the server
```
ssh seat-for-the-sea './deploy-ethertoff.sh'
```

## Copy data from the remote server and load locally
```
ssh seat-for-the-sea './dump-data.sh'
scp seat-for-the-sea:data.json ./
./manage.py loaddata data.json
```

