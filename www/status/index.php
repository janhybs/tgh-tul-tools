<?php session_start();
define('HAS_INDEX', TRUE);

require_once ("../config/config.php");
require_once (ROOT . "/libs.php");

$status = getServiceStatus();
$serviceRunner = $status->runner;
$serviceWatchdog = $status->watchdog;
?>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
    <title>TGH - odevzdání řešení</title>

    <!-- Bootstrap -->
    <link href="<?php echo SERVER_ROOT;?>/css/bootstrap.min.css" rel="stylesheet">
    <link href="<?php echo SERVER_ROOT;?>/css/main.css" rel="stylesheet">
    <link href="<?php echo SERVER_ROOT;?>/css/styles/default.css" rel="stylesheet" >

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
  </head>
  <body>
    <div class="jumbotron" id="wrap">
      <div class="container" id="main-cont">
        <h1>TGH <small data-prefix=" úloha ">Service status</small></h1>

        <h2>Služba pro zpracování řešení<small><?php echo "($status->runnerPidFile:$status->runnerPid)";?></small></h2>
        <div class="progress">
          <div class="progress-bar progress-bar active progress-bar-<?php echo $serviceRunner ? 'success' : 'danger';?>" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%">
            <span class="sr-only">...</span>
          </div>
        </div>

        <br />

        <h2>Služba pro spuštění služby pro zpracování řešení<small><?php echo "($status->watchdogPidFile:$status->watchdogPid)";?></small></h2>
        <div class="progress">
          <div class="progress-bar progress-bar active progress-bar-<?php echo $serviceWatchdog ? 'success' : 'danger'; ?>" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%">
            <span class="sr-only">...</span>
          </div>
        </div>
        
        <br />
        
        <h2>Debug info</h2>
        <code>
          <pre><?php print_r($GLOBALS); ?></pre>
        </code>

      </div>
    </div>



    <footer class="footer">
      <div class="container text-muted">
        <div class="col-md-6">Připomínky zasílejte na jan.hybs (at) tul.cz</div>
        <div class="text-right col-md-6">Veškerý provoz je <strong>monitorován</strong></div>
      </div>
    </footer>
  </body>
      

    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script src="<?php echo SERVER_ROOT;?>/js/jquery-2.1.3.min.js"></script>
    <script src="<?php echo SERVER_ROOT;?>/js/bootstrap.min.js"></script>
    <script src="<?php echo SERVER_ROOT;?>/js/highlight.pack.js"></script>
    <script src="<?php echo SERVER_ROOT;?>/js/main.js"></script>
</html>
