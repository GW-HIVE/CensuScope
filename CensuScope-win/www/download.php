<?php session_save_path($_SERVER['DOCUMENT_ROOT'].'/elect_files/');
session_start();

header('Content-type: application/zip');

header('Content-Disposition: attachment; filename="censuscope-result.zip"');
$output=$_SESSION['output'];

readfile($output);

?> 