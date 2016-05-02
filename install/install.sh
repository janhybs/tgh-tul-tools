#!/bin/bash
# TGH install script

set -x

# root perms
find ../ -type d -exec chmod 775 {} \;
find ../ -type f -exec chmod 664 {} \;
chown -R jan-hybs      ../
chgrp -R devs          ../

# install scripts perms
chmod +x install.sh
chmod +x tgh-service
chmod +x tgh-watchdog

# allow access to data folder only devs and apache
chmod -R 770           ../data
chown -R www-data      ../data
chgrp -R devs          ../data
chown -R jan-hybs      ../data/.readme.md

# access to jobs is for apache and tgh worker
chmod -R 770           ../jobs
chown -R tgh-worker    ../jobs
chgrp -R devs          ../jobs
chown -R jan-hybs      ../jobs/.readme.md

# copy links
cp tgh-service /usr/bin/tgh-service
cp tgh-watchdog /usr/bin/tgh-watchdog