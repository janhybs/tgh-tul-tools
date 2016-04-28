<?php

// define ('ROOT', realpath($_SERVER["DOCUMENT_ROOT"]));
define ('ROOT', realpath($_SERVER["DOCUMENT_ROOT"]) . '/test/tgh');

$config = file_get_contents(ROOT . '/config/config.json');
$jsonConfig = json_decode($config);


define ('JOBS_ROOT',    $jsonConfig->jobs);
define ('DATA_ROOT',    $jsonConfig->data);
define ('PROBLEM_ROOT', $jsonConfig->problems);
define ('CONFIG_ROOT',  $jsonConfig->config);
define ('PYTHON_PATH',  'python2.7');
// define ('ALLOWED_USERS', serialize (array('jan.hybs', 'jan.brezina', 'jiri.hnidek', 'superego')));

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

