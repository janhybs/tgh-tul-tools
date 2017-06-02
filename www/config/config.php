<?php

define ('ROOT',                     '/var/www/html/tgh.nti.tul.cz');
define ('SERVER_ROOT',              'https://tgh.nti.tul.cz');
$config = file_get_contents(ROOT .  '/config/config-tgh.json');

// define ('ROOT', '/var/www/html/test/tgh');
// define ('SERVER_ROOT', 'http://hybs.nti.tul.cz/test/tgh');
// $config = file_get_contents(ROOT . '/config/config-hybs.json');


$jsonConfig = json_decode($config);
define ('JOBS_ROOT',    $jsonConfig->jobs);
define ('DATA_ROOT',    $jsonConfig->data);
define ('PROBLEM_ROOT', $jsonConfig->problems);
define ('CONFIG_ROOT',  $jsonConfig->config);


define('SERVICE_DEBUG', TRUE);
define('MAX_WAIT_TIME', 30+5);

class JobCode {
    const OK                        = 0;
    const RUN_OK                    = 0;
    
    const CORRECT_OUTPUT            = 1;
    const TIMEOUT_CORRECT_OUTPUT    = 3;
    
    const WRONG_OUTPUT              = 5;
    const TIMEOUT_WRONG_OUTPUT      = 7;
    
    const COMPILE_ERROR             = 10;
    const RUN_ERROR                 = 20;
    const TIMEOUT                   = 30;
    const GLOBAL_TIMEOUT            = 40;
    const SKIPPED                   = 50;
    const UNKNOWN_ERROR             = 100;
    
    public static function toString($value) {
        if ($value == JobCode::OK) return 'OK';
        if ($value == JobCode::RUN_OK) return 'OK';
        if ($value == JobCode::CORRECT_OUTPUT) return 'Správný výstup';
        if ($value == JobCode::TIMEOUT_CORRECT_OUTPUT) return 'Správný výstup a překročen časový limit';
        if ($value == JobCode::TIMEOUT_WRONG_OUTPUT) return 'Chybný výstup  a překročen časový limit';
        if ($value == JobCode::WRONG_OUTPUT) return 'Chybný výstup';
        if ($value == JobCode::COMPILE_ERROR) return 'Chyba při kompilaci';
        if ($value == JobCode::RUN_ERROR) return 'Chyba při běhu';
        if ($value == JobCode::TIMEOUT) return 'Úloha nedoržela časový limit';
        if ($value == JobCode::GLOBAL_TIMEOUT) return 'Úloha nedoržela globální časový limit';
        if ($value == JobCode::SKIPPED) return 'Test byl přeskočen';
        return 'Neznámá chyba';
        
    }
}

# debug purpose
# define ('ALLOWED_USERS', serialize (array('jan.hybs', 'jan.brezina', 'jiri.hnidek', 'superego')));
define ('REFERENCE_USERS', serialize (
      array(
        'jan.hybs',
        'jan.brezina'
      )
));

$jsonProblems   = FALSE;
$jsonLangs      = FALSE;

function getLanguages() {
    global $jsonLangs;
    
    if ($jsonLangs !== FALSE)
        return $jsonLangs;

    $data = file_get_contents(CONFIG_ROOT . '/langs.yaml');
    $jsonLangs = array_to_object(yaml_parse($data));
    
    return $jsonLangs;
}


function getProblems() {
    global $jsonProblems;
    
    if ($jsonProblems !== FALSE)
        return $jsonProblems;

    $data = file_get_contents(CONFIG_ROOT . '/problems.yaml');
    $jsonProblems = array_to_object(yaml_parse($data));
    
    return $jsonProblems;
}

