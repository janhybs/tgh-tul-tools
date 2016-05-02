<?php session_start (); ?>

<pre>
<?php


# save user to session
$details = array(
    'Shib-Application-ID',
    'Shib-Session-ID',
    'Shib-Identity-Provider',
    'Shib-Authentication-Instant',
    'Shib-Authentication-Method',
    'Shib-AuthnContext-Class',
    'Shib-Session-Index',
    'affiliation',
    'eppn',
    'persistent-id');

foreach ($details as $key)
    if (isset($_SERVER[$key]))
        $_SESSION["$key"] = $_SERVER[$key];
    else
        header ("Location: /404");
      // die ($key);


# manually parse eppn
$user   = explode ('@', $_SERVER['eppn'], 2);
$user[] = preg_split("/@$user[1];?/i", $_SERVER['affiliation'], -1, PREG_SPLIT_NO_EMPTY);
$user[] = preg_replace('/([^\.]+)\.([^\.]+)/i', '${2}.${1}', $user[0]);

$keys   = array ('username', 'domain', 'groups', 'nameuser');
$user   = array_combine ($keys, $user);

$_SESSION['user'] = (object) $user;

// print_r ($_SESSION);
// die;
header ("Location: /");
?>
