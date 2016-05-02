<?php session_start();
define('HAS_INDEX', TRUE);

require_once ("./config/config.php");
require_once (ROOT . "/libs.php");

$user = auth () or die ();


$errors = array(
    'lang' => 'Nepodporovaný programovací jazyk',
    'problem' => 'Neznámá úloha',
    'perm' => 'Nedostatečná oprávnění k odevzdání referenčního řešení'
);
$error = @$errors[@$_GET['e']];

# try to get values from GET method and then from SESSION
$prefferedProblem   = @$_GET['p'];
$prefferedLang      = @$_GET['l'];
$prefferedSource    = @$_GET['s'];

# test empty GET args and use SESSION instead
$history = @$_SESSION['history'];
if (empty($prefferedProblem)) $prefferedProblem   = @$history->problem;
if (empty($prefferedLang))    $prefferedLang      = @$history->lang;
if (empty($prefferedSource))  $prefferedSource    = @$history->source;
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
          <a class="navbar-brand" href="<?php echo SERVER_ROOT;?>/">TGH</a>
          <?php if(user_allowed_reference($user)): ?>
          <a class="navbar-brand" href="<?php echo SERVER_ROOT;?>/status">STATUS</a>
          <?php endif;?>
        </div>

        <!-- Collect the nav links, forms, and other content for toggling -->
        <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
          <ul class="nav navbar-nav">
          </ul>
          <ul class="nav navbar-nav navbar-right">
            <li><a href="<?php echo SERVER_ROOT;?>/logout"><?php showLogout ($user); ?></a></li>
          </ul>
        </div><!-- /.navbar-collapse -->
      </div><!-- /.container-fluid -->
    </nav>

    <div class="jumbotron" id="wrap">
      <div class="container" id="main-cont">
        <h1>TGH <small data-prefix=" úloha " class="problem-name"></small></h1>

        <div class="alert alert-info" role="alert">
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
            <strong>Aktualizováno 29.5.</strong> Problémy hlaste na: jan.brezina at tul.cz. 
            <a href="http://atrey.karlin.mff.cuni.cz/~morf/vyuka/tgh/index.html" class="alert-link"><span class="glyphicon glyphicon-link" aria-hidden="true"></span>Stránka předmětu TGH</a>
            zadání 2014 a další poznámky
        </div>
        <?php if ($error): ?>
        <div class="alert alert-danger" role="alert">
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
            <strong><?php echo $error; ?></strong>
        </div>
        <?php endif; ?>

        <form name="send-code" action="/test/tgh/result/" method="post" accept-charset="utf-8">

            <label for="selected-problem">Problém</label>
            <div class="input-group">
                <select id="selected-problem" name="selected-problem" class="form-control">

                    <?php foreach (getProblems() as $problem): ?>
                    <option value="<?php echo $problem->id; ?>"<?php echo (strcmp($problem->id, $prefferedProblem) === 0 ? ' selected="selected"' : ''); ?>><?php echo $problem->name; ?></option>
                    <?php echo $prefferedProblem; endforeach; ?>

                </select>
                <a href="<?php echo SERVER_ROOT;?>/problems/" class="btn btn-success btn-large input-group-addon active problem-url" data-prefix="<?php echo SERVER_ROOT;?>/problems/" target="_blank">
                    <span class="glyphicon glyphicon-link" aria-hidden="true"></span>
                    Otevřít zadání pro úlohu
                    <strong class="problem-name"></strong>
                </a>
            </div>

            <label for="selected-language">Programovací jazyk:</label>
            <div class="input-group">
                <select id="selected-language" name="selected-language" class="form-control">

                    <?php foreach (getLanguages() as $lang): ?>
                    <option value="<?php echo $lang->id; ?>"<?php echo (strcmp($lang->id, $prefferedLang) === 0 ? ' selected="selected"' : ''); ?>><?php echo $lang->name; ?> (<?php echo $lang->version; ?>)</option>
                    <?php endforeach; ?>

                </select>

                <a href="#" class="btn btn-info btn-large input-group-addon active lang-url">
                    <span class="glyphicon glyphicon-console" aria-hidden="true"></span>
                    Ukázka v jazyce
                    <strong class="lang-name"></strong>
                </a>
            </div>
            
            <?php if(user_allowed_reference($user)): ?>
            <div class="form-group highlight checkbox">
                <label for="reference-solution">
                    <input name="reference-solution" type="checkbox" class="bigger-checkbox" id="reference-solution">
                    Referenční řešení
                </label>
            </div>
            <?php endif;?>

            <div class="input-group" id="source-code-example-holder" style="display: none;">
                <label for="source-code-example">Ukázka v jazyce <strong class="lang-name"></strong></label>
                <pre><code id="source-code-example"></code></pre>
            </div>

            <div class="form-group">
                <label for="comment">Zdrojový kód:</label>
                <textarea class="form-control" rows="20" name="source-code" id="source-code"><?php echo $prefferedSource; ?></textarea>
            </div>

            <input type="submit" class="btn btn-success btn-large" value="Odevzdat řešení"/>
        </form>
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
