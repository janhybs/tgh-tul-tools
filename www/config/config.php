<?php

// define ('ROOT', realpath($_SERVER["DOCUMENT_ROOT"]));
define ('ROOT', realpath($_SERVER["DOCUMENT_ROOT"]) . '/test/tgh');
define ('SERVER_ROOT', 'http://hybs.nti.tul.cz/test/tgh');
define ('RUN_RUNNER_SERVICE', 'python /home/jan-hybs/Dokumenty/projects/tgh-tul-tools/src/main.py start /home/jan-hybs/Dokumenty/projects/tgh-tul-tools/config/config.json');
// define ('RUN_RUNNER_SERVICE', 'whoami');

$config = file_get_contents(ROOT . '/config/config.json');
$jsonConfig = json_decode($config);


define ('JOBS_ROOT',    $jsonConfig->jobs);
define ('DATA_ROOT',    $jsonConfig->data);
define ('PROBLEM_ROOT', $jsonConfig->problems);
define ('CONFIG_ROOT',  $jsonConfig->config);
define ('PYTHON_PATH',  'python2.7');

class JobResult {
    const OK                = 0;
    const RUN_OK            = 0;
    const CORRECT_OUTPUT    = 1;
    const WRONG_OUTPUT      = 3;
    const COMPILE_ERROR     = 10;
    const RUN_ERROR         = 20;
    const UNKNOWN_ERROR     = 100;
}

// define ('ALLOWED_USERS', serialize (array('jan.hybs', 'jan.brezina', 'jiri.hnidek', 'superego')));
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

    $data = file_get_contents(CONFIG_ROOT . '/langs.json');
    $jsonLangs = json_decode($data);
    
    return $jsonLangs;
}


function getProblems() {
    global $jsonProblems;
    
    if ($jsonProblems !== FALSE)
        return $jsonProblems;

    $data = file_get_contents(CONFIG_ROOT . '/problems.json');
    $jsonProblems = json_decode($data);
    
    return $jsonProblems;
}

