#!/bin/bash
# TGH install script

set -x

# root perms
find ../ -type d -exec chmod 775 {} \;
find ../ -type f -exec chmod 664 {} \;
chown -R root          ../
chgrp -R devs          ../

# install scripts perms
chmod +x install.sh
chmod +x tgh-service
chmod +x tgh-watchdog

# allow access to data folder only devs and apache
chmod -R 770           ../www/data
chown -R apache        ../www/data
chgrp -R devs          ../www/data
chown -R root          ../www/data/.readme.md

# access to jobs is for apache and tgh worker
chmod -R 770           ../www/jobs
chown -R tgh-worker    ../www/jobs
chgrp -R devs          ../www/jobs
chown -R root          ../www/jobs/.readme.md

# copy links
cp tgh-service /usr/bin/tgh-service
cp tgh-watchdog /usr/bin/tgh-watchdog