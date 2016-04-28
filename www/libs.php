<?php

function auth () {
    # no session? go to login section
    if (isset ($_SESSION['user']) && is_object ($_SESSION['user'])) {
        $user = $_SESSION['user'];

        # user check
        if (defined('ALLOWED_USERS')) {
            $users = unserialize (ALLOWED_USERS);
            $username = $user->username;

            # if not in array denied
            if (array_search ($username, $users) === FALSE)
                header ("Location: /denied");
        }

        return $user;

    } else
        header("Location: /secure");
    die ('just in case');
}

function user_allowed_reference($user) {
    $users = array('jan.hybs', 'jan.brezina');
    return in_array($user->username, $users);
}


function mkdirs ($location, $mode = 0774) {
    if (is_dir($location))
        return;

    $old = umask (000); 
    mkdir ($location, $mode, true); 
    umask ($old); 
}


function runService () {
    @file_put_contents('/var/www/html/tgh.nti.tul.cz/jobs/watchdog', 'delete-me');
}

function getServiceStatus() {
    $pidRunner          = intval(@file_get_contents('/tmp/tgh-runner.pid'));
    $pidRunner_         = intval(exec ("ps -p $pidRunner -o pid,state --no-headers"));
    $pidWatchdog        = intval(@file_get_contents('/tmp/tgh-watchdog.pid'));
    $pidWatchdog_       = intval(exec ("ps -p $pidWatchdog -o pid,state --no-headers"));

    $serviceRunner      = ($pidRunner === $pidRunner_) && $pidRunner_ > 0;
    $serviceWatchdog    = ($pidWatchdog === $pidWatchdog_) && $pidWatchdog > 0;
    
    $result = (object)array();
    $result->runner = $serviceRunner;
    $result->watchdog = $serviceWatchdog;
    return  $result;
}


function get_data_path($tempFile, $dataDir, $f='/output/') {
    $name = basename($tempFile);
    return $dataDir . $f . $name;
}


function waitForResult ($job) {
    $lockFile = join_paths($job->root, '.delete-me');
    $resultFile = join_paths($job->root, 'result.json');
    $time = 0;
    $graceful = FALSE;
    
    $serviceStatus = getServiceStatus();
    
    // if (!$serviceStatus->runner && !$serviceStatus->watchdog) {
    //     throw new Exception('Processing service and Watchdog services are both dead. Please contact <a href="mailto:jan.hybs@tul.cz">jan.hybs</a> to make them work again');
    // }
    
    if (!$serviceStatus->runner) {
        runService();
        throw new Exception('Processing service is down. Try to send your code again in few minutes (It takes approx 1 minute for service to kick in).');
    }
    
    # wait for file to get deleted
    while($time < 10) {
        if (!file_exists($lockFile) && file_exists($resultFile)) {
            $graceful = TRUE;
            break;
        }
        
        sleep(2);
        $time += 2; 
    }
    
    if ($graceful) {
        return json_decode(file_get_contents($resultFile));
    }
    throw new Exception('Service did not respond within the timeout period. If problem remains, please contact <strong>jan.hybs (at) tul.cz</strong>');
    
    // # no response in 60sec
    // # something even worse happened
    // if ($serviceIsDead) {
    //     return (object)array('exit' => -1, 'result' => 'Server did not respond within the timeout period. <br />It means that there was issue on server. Please try again in couple minutes.<br />If problem remains, please contact <strong>jan.hybs (at) tul.cz</strong>');
    // }
    // return (object)array('exit' => -1, 'result' => 'Server did not respond within the timeout period. <br />It probably means that code execution took longer than 1 minute. <br />If problem remains, please contact <strong>jan.hybs (at) tul.cz</strong>');

}

function rrmdir($dir) { 
   if (is_dir($dir)) { 
     $objects = scandir($dir); 
     foreach ($objects as $object) { 
       if ($object != "." && $object != "..") { 
         if (filetype($dir."/".$object) == "dir") rrmdir($dir."/".$object); else unlink($dir."/".$object); 
       } 
     } 
     reset($objects); 
     rmdir($dir); 
   } 
} 

function cleanJobFiles ($jobInfo) {
    // rrmdir ($jobDir);
}


function showLogout ($user) {
    ?>
        Logout <strong><?php echo $user->username; ?></strong>@<strong><?php echo $user->domain; ?></strong><br />
        <small><?php echo implode (', ', $user->groups); ?></small>
    <?php
}


function getFileSizeString ($filename) {
    $size = @filesize ($filename);
    if ($size === FALSE)
        return 'file does not exists';

    if ($size === 0)
        return 'file is empty';

    if ($size < 800)
        return sprintf("%d B", $size);

    if ($size < (100*1024))
        return sprintf("%1.2f kB", $size / (1024));

    if ($size < (100*1024*1024))
        return sprintf("%1.2f MB", $size / (1024*1024));

    if ($size < (100*1024*1024*1024))
        return sprintf("%1.2f gB", $size / (1024*1024*1024));

    return "file is too large";
}