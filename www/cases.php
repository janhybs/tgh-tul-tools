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


$languages = getLanguages();
$problems = getProblems();
$canRef = user_allowed_reference($user);



$lang = @$_POST['selected-language'];
$problem = @$_POST['selected-problem'];
$source = @$_POST['source-code'];
$ref = !empty($_POST['reference-solution']);
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

echo '<pre>';
// isset($_SESSION);
echo '</pre>';

?>
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="shortcut icon" href="favicon.ico" type="image/x-icon" >
    <link rel="icon" type="image/png" href="favicon.png" />
    <!-- The above 3 meta tags *must* come first in the head; any other head content must come *after* these tags -->
    <title>TGH - odevzdání řešení</title>

    <!-- Bootstrap -->
    <link href="<?php echo SERVER_ROOT;?>/css/bootstrap.min.css" rel="stylesheet" >
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

        <?php if ($error): ?>
        <div class="alert alert-danger" role="alert">
            <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                <span aria-hidden="true">&times;</span>
            </button>
            <strong><?php echo $error; ?></strong>
        </div>
        <?php endif; ?>
        
        <?php if(!getProblems()): ?>
            <big>
                <div class="alert alert-danger">
                    <strong>Error</strong> Problém při načítání konfiguračního souboru <code>problems.json</code>
                </div>
            </big>
        <?php elseif (!getLanguages()): ?>
            <big>
                <div class="alert alert-danger">
                    <strong>Error</strong> Problém při načítání konfiguračního souboru <code>langs.json</code>
                </div>
            </big>
        <?php else: ?>
            <div class="alert alert-info" role="alert">
                <button type="button" class="close" data-dismiss="alert" aria-label="Close">
                    <span aria-hidden="true">&times;</span>
                </button>
                <strong>Aktualizováno 20.5.2016</strong> Problémy hlaste na: jan.brezina at tul.cz. 
                <a href="http://atrey.karlin.mff.cuni.cz/~morf/vyuka/tgh/index.html" class="alert-link"><span class="glyphicon glyphicon-link" aria-hidden="true"></span>Stránka předmětu TGH</a>
            </div>
            
            <form name="send-code" action="<?php echo SERVER_ROOT;?>/result/" method="post" accept-charset="utf-8">
                <input type="hidden" name="selected-problem" value="<?php echo $problem; ?>" />
                <input type="hidden" name="selected-language" value="<?php echo $lang; ?>" />
                <input type="hidden" name="reference-solution" value="<?php echo $ref; ?>" />
                <textarea class="form-control" rows="20" name="source-code" id="source-code" style="display: none;"><?php echo $source; ?></textarea>
                
                
                <?php if (!$ref): ?>
                    <div class="input-group" id="test-cases">
                        <label for="test-cases">Zvolte testy, které chcete spustit: </label>
                        <?php foreach ($problemInfo->input as $input): ?>
                            <div class="checkbox">
                              <label>
                                <input type="checkbox" name="selected-cases[]" value="<?php echo $input->id; ?>" checked>
                                <?php echo $input->id; ?> (časový limit: <?php echo $input->time; ?>s<?php if (isset($input->problem_size)): ?>, velikost dat: <?php echo $input->problem_size; ?><?php endif; ?>) 
                              </label>
                            </div>
                        <?php endforeach; ?>
                    </div>
                <?php endif; ?>
                
                <?php if (!$ref): ?>
                    <input type="submit" class="btn btn-success btn-large" value="Odevzdat řešení"/>
                <?php else: ?>
                    <input type="submit" class="btn btn-success btn-large" value="Vygenerovat referenční řešení"/>
                <?php endif; ?>


                <div class="input-group" id="source-code">
                    <label for="source-code">Zdrojový kód (<strong class="lang-name"></strong>): </label>
                    <pre><code id="source-code"><?php echo $source; ?></code></pre>
                </div>


            </form>
        <?php endif; ?>
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
