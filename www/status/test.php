<?php

$dir =  "/var/www/html/tgh.nti.tul.cz/jobs/job-jan.hybs_1462185323.7282_6483";
mkdir($dir, 0777);
file_put_contents("$dir/foo.txt", "txt");
