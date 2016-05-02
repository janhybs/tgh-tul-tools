<?php session_start();
define('HAS_INDEX', TRUE);

require_once ("./config/config.php");
require_once (ROOT . "/libs.php");

$user = auth () or die ();

$languages = getLanguages();
$problems = getProblems();
$canRef = user_allowed_reference($user);



$lang = @$_POST['selected-language'];
$problem = @$_POST['selected-problem'];
$source = @$_POST['source-code'];
$ref = isset($_POST['reference-solution']);
$username = $user->username;

# save recent source-code task and more
$history = (object)array();
$history->source    = $source;
$history->lang      = $lang;
$history->problem   = $problem;
$_SESSION['history'] = $history;


if (! isset ($_POST['selected-language'], $_POST['selected-problem'], $_POST['source-code']))
  redirect("");

# language check
if (!isset($languages->$lang))
    redirect("?e=lang");
$langInfo = (object)$languages->$lang;

# problem check
if (!isset($problems->$problem))
    redirect("?e=problem");
$problemInfo = (object)$problems->$problem;

# permission check
if(!$canRef && $ref) {
    redirect('?e=perm');
}

# prepare job request
$jobInfo = (object)array();
$jobInfo->root = JOBS_ROOT . '/' . sprintf("job-%s_%s_%s", $username, microtime(true), rand(1, 10*1000));
$jobInfo->timestamp = time();
$jobInfo->filename = "main." . $languages->$lang->extension;
$jobInfo->username = $user->username;
$jobInfo->nameuser = $user->nameuser;

$jobInfo->lang_id = $languages->$lang->id;
$jobInfo->problem_id = $problems->$problem->id;
$jobInfo->reference = $ref ? TRUE : FALSE;


# write files
mkdirs ($jobInfo->root, 0777);
$jsonInfo = defined('JSON_PRETTY_PRINT') ? json_encode($jobInfo, JSON_PRETTY_PRINT) : json_encode($jobInfo);
file_put_contents("$jobInfo->root/" . $jobInfo->filename, $source);
file_put_contents("$jobInfo->root/config.json", $jsonInfo);
file_put_contents("$jobInfo->root/.delete-me", 'Python will delete me!');

# get service statuses
$status = getServiceStatus();
if (SERVICE_DEBUG)
    $status->runner = TRUE;

// ob_end_flush();
// ob_start();
?>

<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
    <title>TGH - zpracování</title>

    <!-- Bootstrap -->
    <link href="<?php echo SERVER_ROOT;?>/css/bootstrap.min.css" rel="stylesheet">
    <link href="<?php echo SERVER_ROOT;?>/css/styles/default.css" rel="stylesheet" >
    <link href="<?php echo SERVER_ROOT;?>/css/main.css" rel="stylesheet">

    <!-- HTML5 shim and Respond.js for IE8 support of HTML5 elements and media queries -->
    <!-- WARNING: Respond.js doesn't work if you view the page via file:// -->
    <!--[if lt IE 9]>
      <script src="https://oss.maxcdn.com/html5shiv/3.7.2/html5shiv.min.js"></script>
      <script src="https://oss.maxcdn.com/respond/1.4.2/respond.min.js"></script>
    <![endif]-->
  </head>
  <body>
    <nav class="navbar navbar-default">
      <div class="container-fluid">
        <!-- Brand and toggle get grouped for better mobile display -->
        <div class="navbar-header">
          <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1">
            <span class="sr-only">Toggle nav</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
          </button>
          <a class="navbar-brand" href="<?php echo SERVER_ROOT;?>">TGH</a>
        </div>

        <!-- Collect the nav links, forms, and other content for toggling -->
        <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
          <ul class="nav navbar-nav">
          </ul>
          <ul class="nav navbar-nav navbar-right">
            <li><a href="/logout"><?php showLogout ($user); ?></a></li>
          </ul>
        </div><!-- /.navbar-collapse -->
      </div><!-- /.container-fluid -->
    </nav>

    <div class="jumbotron">
      <div class="container" id="main-cont">
        <h1><a href='<?php echo SERVER_ROOT; ?>' title="Upravit zdrojový kód" class="btn btn-default btn-lg">
              <span class="glyphicon glyphicon-chevron-left" aria-hidden="true">
            </a>
            TGH <small data-prefix=" úloha " class="problem-name"><?php echo $problemInfo->id; ?></small>
        </h1>


        <?php if (!$status->runner): ?>
          <?php
            cleanJobFiles($jobInfo);
          ?>
          <div class="has-error">
              <h4>Služba pro zpracování neběží</h4>
              <div class="alert alert-danger info" role="alert">
                <p>
                    Služba, která slouží pro zpracování odevzdaných řešení neběží a vyžaduje
                     restart. Celý proces restartování může trvat až několik minut.
                </p>
                <p>
                    Zkuste prosím zaslat řešení znovu za pár minut a pokud bude problém přetrvávat, 
                    kontaktuje <a class="alert-link" href="mailto:jan.hybs@tul.cz?subject=TGH-service-down">jan.hybs(at)tul.cz</a>
                </p>
              </div>
            </div>
          <h4>Odevzdaný zdrojový kód</h4>
          <pre><?php echo $source; ?></pre>
        <?php else: ?>

        <div class="well" id="processing">Probíhá zpracování...
          <div class="progress">
            <div class="progress-bar progress-bar-success progress-bar-striped active" role="progressbar" aria-valuenow="100" aria-valuemin="0" aria-valuemax="100" style="width: 100%">
              <span class="sr-only">running</span>
            </div>
          </div>
        </div>

        <div class="alert alert-success" role="alert" id="output-holder" style="display: block;">
          <strong id="output-header">Probíhá zpracování úlohy</strong>
            <?php 
                // ob_implicit_flush(1);
                // ob_start();
                ob_flush();
                flush();
                
                $result = waitForResult($jobInfo);
                // cleanJobFiles($jobInfo);
                // print_r($result);
                // print ("<code id='result-summary'>$result->summary</code>");
                print ("<span id='exit-code' style='display: none;'>$result->max_result</span>");
             ?>
             <table class="table table-striped table-hover">
               <tr>
                 <th>sada</th>
                 <th>result</th>
                 <th>duration</th>
                 <th>io</th>
                 <th>details</th>
               </tr>
               <?php foreach (@$result->result as $res):
                    $cls = @$res->result <= JobResult::CORRECT_OUTPUT ? ' class="success"' : ' class="danger"';
                    ?>
                   <tr<?php echo $cls?>>
                     <td><?php echo @$res->info->id; ?></td>
                     <td><?php echo JobResult::toString(@$res->result); ?></td>
                     <td><?php printf("%1.3f ms", @$res->duration); ?></td>
                     <td>
                         <div class="btn-group" role="group" aria-label="...">
                         <?php if(@$res->input): ?>
                           <a target="_blank" class="btn btn-default" href="<?php echo path2url(@$res->input);?>">I</a>
                         <?php else: ?>
                            <a target="_blank" class="btn btn-default disabled" href="">I</a>
                         <?php endif; ?>
                         
                           <a target="_blank" class="btn btn-default" href="<?php echo path2url(get_data_path(@$res->output, @$result->attempt_dir));?>">O</a>
                         </div>
                     </td>
                     <td><?php 
                            if ($ref) {
                                if (@$res->info->problem_size) {
                                    echo " -p ";
                                    echo @$res->info->problem_size;
                                    if (@$res->info->random) {
                                        echo " -r";
                                    }
                                }
                            } else {
                                if (@$res->result >= JobResult::CORRECT_OUTPUT) {
                                    echo "<pre>";
                                    echo @$res->method;
                                    if (!empty($res->error))
                                        echo ": " . @$res->error;
                                    if (!empty($res->comparison)) {
                                        if (is_object(@$res->comparison)) {
                                            echo defined('JSON_PRETTY_PRINT') ? json_encode(@$res->comparison, JSON_PRETTY_PRINT) : json_encode(@$res->comparison);
                                        }else{
                                            print_r(@$res->comparison);
                                        }
                                        echo "</pre>";
                                    }
                                }
                            }
                         ?>
                    </td>
                   </tr>
               <?php endforeach; ?>
             </table>
       </div>
      </div>
    </div>

  <?php endif; ?>

    <footer class="footer">
      <div class="container text-muted">
        <div class="col-md-6">Připomínky zasílejte na jan.hybs (at) tul.cz</div>
        <div class="text-right col-md-6">Veškerý provoz je <strong>monitorován</strong></div>
      </div>
    </footer>

    <!-- jQuery (necessary for Bootstrap's JavaScript plugins) -->
    <script type="text/javascript" src="<?php echo SERVER_ROOT;?>/js/jquery-2.1.3.min.js"></script>
    <script type="text/javascript" src="<?php echo SERVER_ROOT;?>/js/bootstrap.min.js"></script>
    <script type="text/javascript" src="<?php echo SERVER_ROOT;?>/js/highlight.pack.js"></script>
    <script type="text/javascript">hljs.initHighlighting()</script>
    <script type="text/javascript" src="<?php echo SERVER_ROOT;?>/js/res.js"></script>

  </body>
</html>
