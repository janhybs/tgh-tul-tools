<?php
define ('ROOT', realpath($_SERVER["DOCUMENT_ROOT"]));
define ('JOBS_ROOT',  ROOT . "/jobs");
define ('DATA_ROOT',  ROOT . "/data");
define ('PROBLEM_ROOT', ROOT . "/problems");
define ('PYTHON_PATH', 'python2.7');
// define ('ALLOWED_USERS', serialize (array('jan.hybs', 'jan.brezina', 'jiri.hnidek', 'superego')));

$jsonProblems = FALSE;

function arrayToObject ($array) { return json_decode (json_encode ($array));}

function getLanguages () {
    $v =  array(
        "cs"        => array("id" => "cs",       "extension" => "cs",    "name" => 'C#',     "version" => 'Mono 3.0.7'),
        "c"         => array("id" => "c",        "extension" => "c",     "name" => 'C',      "version" => 'gcc 4.7.2.5'),
        "cpp"       => array("id" => "cpp",      "extension" => "cpp",   "name" => 'C++',    "version" => 'g++ 4.7.2.5'),
        "java"      => array("id" => "java",     "extension" => "java",  "name" => 'Java',   "version" => 'java 1.8.0_45'),
        "pascal"    => array("id" => "pascal",   "extension" => "pas",   "name" => 'Pascal', "version" => 'fpc 2.4.0'),
        "python27"  => array("id" => "python27", "extension" => "py",    "name" => 'Python', "version" => 'python 2.7.6')
    );
    return arrayToObject($v);
}


function getProblems () {
    global $jsonProblems;
    
    if ($jsonProblems !== FALSE)
        return $jsonProblems;

    $data = file_get_contents (ROOT . '/cfg/problems.json');
    $jsonProblems = json_decode ($data);
    
    return $jsonProblems;
}



