#!/bin/bash
# TGH install script

set -x

usr="root"
# usr="jan-hybs"

apa="apache"
# apa="www-data"

# root perms
find ../ -type d -exec chmod 775 {} \;
find ../ -type f -exec chmod 664 {} \;
chown -R $usr          ../
chgrp -R devs          ../

# install scripts perms
chmod +x install.sh
chmod +x tgh-service
chmod +x tgh-watchdog

# allow access to data folder only devs and apache
chmod -R 777           ../www/data
chown -R $apa          ../www/data
chgrp -R devs          ../www/data
chown -R $usr          ../www/data/.readme.md

# access to jobs is for apache and tgh worker
chmod -R 777           ../www/jobs
chown -R tgh-worker    ../www/jobs
chgrp -R devs          ../www/jobs
chown -R $usr          ../www/jobs/.readme.md

# copy links
cp tgh-service /usr/bin/tgh-service
cp tgh-watchdog /usr/bin/tgh-watchdog