<?php
if (!defined('HAS_INDEX')) die('Forbidden to this page directly.');

function auth () {
    # no session? go to login section
    if (isset ($_SESSION['user']) && is_object ($_SESSION['user'])) {
        $user = $_SESSION['user'];

        # user check for debug
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
    $users = unserialize(REFERENCE_USERS);
    return in_array($user->username, $users);
}

function redirect($args="") {
  $url =  SERVER_ROOT . $args;
  header("Location: $url");
}

function mkdirs ($location, $mode = 0774) {
    if (is_dir($location))
        return;

    $old = umask (000); 
    mkdir ($location, $mode, true); 
    umask ($old); 
}

function getServiceStatus() {
    $pidRunner          = intval(@file_get_contents('/tmp/tgh-runner.pid'));
    $pidRunner_         = intval(exec ("ps -p $pidRunner -o pid,state --no-headers"));
    $pidWatchdog        = intval(@file_get_contents('/tmp/tgh-watchdog.pid'));
    $pidWatchdog_       = intval(exec ("ps -p $pidWatchdog -o pid,state --no-headers"));

    $serviceRunner      = ($pidRunner === $pidRunner_) && $pidRunner_ > 0;
    $serviceWatchdog    = ($pidWatchdog === $pidWatchdog_) && $pidWatchdog > 0;
    
    $result = (object)array();
    
    $result->runner           = $serviceRunner;
    $result->watchdog         = $serviceWatchdog;
    
    $result->runnerPid        = $pidRunner;
    $result->watchdogPid      = $pidWatchdog;
    
    $result->runnerPidFile    = '/tmp/tgh-runner.pid';
    $result->watchdogPidFile  = '/tmp/tgh-watchdog.pid';
    return  $result;
}

function join_paths() {
    $paths = array();
    foreach (func_get_args() as $arg) {
        if ($arg !== '') { $paths[] = $arg; }
    }
    return preg_replace('#/+#','/',join('/', $paths));
}


function get_download_button($url, $link, $alt, $hide=FALSE, $cls="") {
    if (!$url)
        return $hide ? '' : "<a href=\"#\" class=\"btn btn-default $cls disabled\" target=\"_blank\" title=\"Soubor neexistuje\">$link</a>";
    
    return "<a href=\"$url\" class=\"btn btn-default $cls\" target=\"_blank\" title=\"$alt\">$link</a>";
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
    
    
    # wait for file to get deleted
    while($time < MAX_WAIT_TIME) {
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
    
    if (!getServiceStatus()->runner) {
        throw new Exception('Služba neodpověděla v daném časovém úseku jelikož služba něběží. Je ale možné, že se na serveru provádí údržba. Pokud problém do několika minut nezmizí, kontaktujte <strong>jan.hybs(at)tul.cz</strong>');
    }
    
    throw new Exception('Služba neodpověděla v daném časovém úseku. To může být způsobeno následujícím: '.
                        '<ul>'.
                            '<li>Odeslané řešení netihlo dokončit úlohu ve vymezené době</li>'.
                            '<li>Interní chyba serveru</li>'.
                        '</ul>'.
                        ' Pokud problém přetrvá, kontaktujte <strong>jan.hybs(at)tul.cz</strong>');
    
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
    rrmdir ($jobInfo->root);
}


function showLogout ($user) {
    ?>
        Logout <strong><?php echo $user->username; ?></strong>@<strong><?php echo $user->domain; ?></strong><br />
        <small><?php echo implode (', ', $user->groups); ?></small>
    <?php
}


function getFileSizeString ($filename) {
    $size = @filesize ($filename);
    if ($size === FALSE || !is_file($filename))
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

class JobJson {
    
    public $json = null;
    public $job = null;
    
    public $attempt_dir = null;
    public $tmp_dir = null;
    public $reference = null;
    public $max_result = null;
    
    public $is_valid = FALSE;
    public $error = FALSE;
    
    public $results = null;
    
    public static function get($obj, $prop, $default=null) {
        if (isset($obj->$prop))
            return $obj->$prop;
        return $default;
    }
    
    public function getHref($url) {
        if ($url === NULL)
            return NULL;
        return str_replace(ROOT, SERVER_ROOT, $url);
    }
    
    
    function __construct($json, $job) {
        $this->json = $json;
        $this->job  = $job;
        
        $this->error        = JobJson::get($json, 'error', '');
        $this->is_valid     = $this->error === '';
        
        $this->attempt_dir  = JobJson::get($json, 'attempt_dir');
        $this->max_result   = JobJson::get($json, 'max_result');
        $this->tmp_dir      = JobJson::get($job, 'tmp_dir');
        $this->reference    = JobJson::get($job, 'reference');
        $this->results      = array();
        
        $results            = JobJson::get($json, 'result', array());
        if (is_array($results)) {
            foreach ($results as $key => $result) {
                array_push($this->results, new JobJsonResult($this, $result));
            }
        }
    }
}

class JobJsonResult {
    
    function __construct($jobJson, $resultJson) {
        
        # info block
        $info = (object)JobJson::get($resultJson, 'info', array());
        
        $this->case_id = JobJson::get($info, 'case_id');
        $this->problem_random = JobJson::get($info, 'problem_random');
        $this->problem_size = JobJson::get($info, 'problem_size');
        $this->command = JobJson::get($info, 'command');
        
        # result block
        $result = (object)JobJson::get($resultJson, 'result', array());
        
        $this->code = JobJson::get($result, 'code', JobCode::UNKNOWN_ERROR);
        $this->name = JobJson::get($result, 'name', 'unknown');
        $this->duration = JobJson::get($result, 'duration', 0.0);
        $this->returncode = JobJson::get($result, 'returncode', 0);
        $this->details = JobJson::get($result, 'details');
        
        # files block
        $files = (object)JobJson::get($resultJson, 'files', array());
        
        $this->input_href = $jobJson->getHref(JobJson::get($files->input, 'server'));
        $this->output_href = $jobJson->getHref(JobJson::get($files->output, 'server'));
        $this->error_href = $jobJson->getHref(JobJson::get($files->error, 'server'));
        $this->reference_href = $jobJson->getHref(JobJson::get($files->reference, 'server'));
        $this->error = JobJson::get($files->error, 'content', '');
        
        # string representation
         $this->result_str = JobCode::toString($this->code);
         $this->duration_str = sprintf("%1.3f ms", $this->duration);
         
         $this->command_str  = explode( '/', preg_replace('/["\']+/i', '', $this->command));
         $this->command_str  = end($this->command_str);
         
         $this->class_str = $this->code <= JobCode::TIMEOUT_CORRECT_OUTPUT ? 'success' : 'danger';
         $this->class_str = $this->code == JobCode::SKIPPED ? 'warning' : $this->class_str;
         
         # building details
         $this->details = empty($this->command_str) ? "<žádné informace>" : $this->command_str;
         $this->details = empty($this->error) ? $this->details : $this->details . "\nError: $this->error";
    }
}

function format_json($json_, $html = false, $tabspaces = null) {
    $json = json_encode($json_);
    $tabcount = 0;
    $result = '';
    $inquote = false;
    $ignorenext = false;

    if ($html) {
        $tab = str_repeat("&nbsp;", ($tabspaces == null ? 4 : $tabspaces));
        $newline = "<br/>";
    } else {
        $tab = ($tabspaces == null ? "\t" : str_repeat(" ", $tabspaces));
        $newline = "\n";
    }

    for($i = 0; $i < strlen($json); $i++) {
        $char = $json[$i];

        if ($ignorenext) {
            $result .= $char;
            $ignorenext = false;
        } else {
            switch($char) {
                case ':':
                    $result .= $char . (!$inquote ? " " : "");
                    break;
                case '{':
                    if (!$inquote) {
                        $tabcount++;
                        $result .= $char . $newline . str_repeat($tab, $tabcount);
                    }
                    else {
                        $result .= $char;
                    }
                    break;
                case '}':
                    if (!$inquote) {
                        $tabcount--;
                        $result = trim($result) . $newline . str_repeat($tab, $tabcount) . $char;
                    }
                    else {
                        $result .= $char;
                    }
                    break;
                case ',':
                    if (!$inquote) {
                        $result .= $char . $newline . str_repeat($tab, $tabcount);
                    }
                    else {
                        $result .= $char;
                    }
                    break;
                case '"':
                    $inquote = !$inquote;
                    $result .= $char;
                    break;
                case '\\':
                    if ($inquote) $ignorenext = true;
                    $result .= $char;
                    break;
                default:
                    $result .= $char;
            }
        }
    }

    return $result;
}


function replace_extension($url, $ext) {
    if (!$url)
        return $url;
    return preg_replace('/\.[^.]+$/', $ext, $url);
}