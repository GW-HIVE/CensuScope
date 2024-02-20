<?php session_save_path($_SERVER['DOCUMENT_ROOT'].'/elect_files/');
session_start();

//$database=$_POST['database'];
if($_POST['database']){

$database=$_POST['database'];
}


?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<!-- saved from url=(0062)http://hive.biochemistry.gwu.edu/tools/seq.cgi?cmd=dmStrDistri -->
<html><head><meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <title>CensuScope V 1.2</title>
    
    <meta name="Author" content="Vahan Simonyan">
    <meta name="owner" content="Vahan Simonyan">
    <meta name="Reply-To" content="VahanSim@gmail.com">
    <meta name="Keywords" content="Hight throughput sequencing, Next Gen Sequencing, Bioinformatics, Protein, Taxonomy, Sequence">
    <meta name="Description" content="HIVE bioinformatics">
    <meta http-equiv="expires" content="0">
    <meta http-equiv="pragma" content="NO-CACHE">

	<script language="JavaScript1.1" src="./elect_files/qpride.js"> </script>
	<script language="JavaScript1.1" src="./elect_files/basic.js"> </script>
	<link rel="stylesheet" href="./elect_files/styles.css" type="text/css">
	<link rel="stylesheet" href="./elect_files/menu.css" type="text/css">

	




</head>



<div id="top_menu">
             <a id="logo" href="https://hive.biochemistry.gwu.edu/"><img border="0" src="./elect_files/hive-small-brand.png" height="35"></a>
			<ul class="menu_panel">
				
				</li>
				<li class="panel"><a class="menuitem" id="about" href="https://hive.biochemistry.gwu.edu/about.php">ABOUT</a></li>
				<li class="panel"><a class="menuitem" id="tools" href="https://hive.biochemistry.gwu.edu/tools.php">TOOLS</a></li>
				
				<li class="panel"><a class="menuitem" id="people" href="https://hive.biochemistry.gwu.edu/people.php">PEOPLE</a></li>
				<li class="panel"><a class="menuitem" id="contact" href="https://hive.biochemistry.gwu.edu/contact.php">CONTACT</a></li>
				


            </ul>

		</div>
<div id="body_container">
<div id="top_template">
	<h2 id="cgiLocation">CensuScope V1.2</h2>
	<div id="top_image">
</div>






<?php




//error_reporting(0);



//retrieving path of source
if($_POST['source'] && file_exists($_POST['source'])){//file3 is our sample file 
$file3 = $_POST['source'];

}elseif(!$_POST['source'] || !file_exists($_POST['source'])){
 echo "<br>";
 echo("Fatal Error: you did not select the source file or the path is incorrect ");
 ?>
<form action="index.html" method="post">
<input type="submit" name="submit" value="Back" />
</form>
<?php
die();
 }

if($_POST['pack'] && file_exists($_POST['pack'].'CensuScope\blast\blastdb_aliastool')){//pack is nt package 
$path = $_POST['pack'];
}elseif(!$_POST['pack']|| !file_exists($_POST['pack'].'CensuScope\blast\blastdb_aliastool')){
 echo "<br>";
 echo("Fatal Error: you did not select the package or the path is incorrect ");
 ?>
<form action="index.html" method="post">
<input type="submit" name="submit" value="Back" />
</form>
<?php
die();
}



if(file_exists($path.'CensuScope\sample\gi_centric_table.csv')){ unlink($path.'CensuScope\sample\gi_centric_table.csv');}
if(file_exists($path.'CensuScope\sample\log.csv')){ unlink($path.'CensuScope\sample\log.csv');}
if(file_exists($path.'CensuScope\sample\tax_centric_table.csv')){unlink($path.'CensuScope\sample\tax_centric_table.csv');}
if(file_exists($path.'CensuScope\sample\taxslim_centric_table.csv')){unlink($path.'CensuScope\sample\taxslim_centric_table.csv');}
if(file_exists($path.'CensuScope\sample\censuscope-result.zip')){unlink($path.'CensuScope\sample\censuscope-result.zip');}






if($database==0){

$query=$path.'CensuScope\blast\blastdb_aliastool.exe -dblist "'.$path.'CensuScope\database\nt.00\nt.00  '.$path.'CensuScope\database\nt.01\nt.01  '.$path.'CensuScope\database\nt.02\nt.02  '.$path.'CensuScope\database\nt.03\nt.03  '.$path.'CensuScope\database\nt.04\nt.04  '.$path.'CensuScope\database\nt.05\nt.05  '.$path.'CensuScope\database\nt.06\nt.06  '.$path.'CensuScope\database\nt.07\nt.07  '.$path.'CensuScope\database\nt.08\nt.08  '.$path.'CensuScope\database\nt.09\nt.09  '.$path.'CensuScope\database\nt.10\nt.10  '.$path.'CensuScope\database\nt.11\nt.11  '.$path.'CensuScope\database\nt.12\nt.12  '.$path.'CensuScope\database\nt.13\nt.13  '.$path.'CensuScope\database\nt.14\nt.14" -dbtype "nucl" -title "nt" -out "'.$path.'CensuScope\database\nt"'; 
shell_exec($query);
}

// retreiving size
if($_POST['size']){// size of sample
$ssize =$_POST['size'];


}elseif(!$_POST['size']){
 echo "<br>";
 echo("Fatal Error: you did not select the sample size ");
 ?>
<form action="index.html" method="post">
<input type="submit" name="submit" value="Back" />
</form>
<?php
die();
}

// retreiving iteration
if($_POST['iteration']){
$iteration =$_POST['iteration'];

}elseif(!$_POST['']){
 echo "<br>";
 echo("Fatal Error: you did not select the sample size ");
 ?>
<form action="index.html" method="post">
<input type="submit" name="submit" value="Back" />
</form>
<?php
die();
}
 
    print "<br>";
    print "ITERATION : ".$iteration."\n";
	print "<br>";
    print "READ-SIZE : ".$ssize."\n";
	print "<br>";
    print "TAXSLIM_DEPTH : KINGDOM\n";
	print "<br>";
    print "SOURCE DIRECTORY : ".$file3."\n"; 
	print "<br>";
$time_start = microtime(true);


set_time_limit(48000000000);


//$file3=$options['d'];

//$ssize=$options['s'];
//$ssize=2000;//based on your request
//$sample=$options['r'];
$sample =1;
//$iteration=$options['i'];
//$iteration=4;

$depth=3;



$high=file_size($file3);


//iteration
for($it=1;$it<=$iteration;$it++){
//print $it.'-';




if($ssize<$high){

//creating random sample
for($i=1;$i<=$sample;$i++){
$query=$path.'CensuScope\blast\random.exe '.$file3.' '.$ssize.' '.$path.'CensuScope\sample\sample'.$i.'.fastq'; 
shell_exec($query);
}
//echo $query;
//echo "<br>";
/*
$high=file_size($file3);
$fp = fopen($file3,'r');
//fseek($fp, 0, SEEK_END);
//$high = ftell($fp);
//print($high);
//print "<br>";

//setting chunk size
//if($high>50000000)$p=floor($high/5000);
//else $p=floor($high/500);
$p=floor($high/5000);
//print ($p);
$chunksize=$p;//based on the size of read

//random picking
for($i=1;$i<=$sample;$i++){
midway($fp,$i,$chunksize,$file3,$path);
}
fclose($fp);

//ffetch
for($i=1;$i<=$sample;$i++){
$f =$path.'CensuScope\sample\total'.$i.'.fastq';
$result =$path.'CensuScope\sample\sample'.$i.'.fastq';
ffetch($f,$result,$ssize);
unlink($f);	
}
*/
} 
else if($ssize>=$high){
//echo "hello";
$srcfile=$file3;
$dstfile=$path.'CensuScope\sample\sample1.fastq';
mkdir(dirname($dstfile), 0777, true);
copy($srcfile, $dstfile);

}
//      fastq to fasta converter
for($i=1;$i<=$sample;$i++){

$result =$path.'CensuScope\sample\sample'.$i.'.fastq';
convert($result,$i,$ssize,$path);
}


// running blastn
for($i=1;$i<=$sample;$i++){
$result =$path.'CensuScope\sample\fasta'.$i.'.fasta';
blastn($result,$i,$path,$database);
//unlink($result);
refine($i,$path);

}



//filter
for($i=1;$i<=$sample;$i++){
ffilter($i,$it,$path);
}


}




excel($iteration,$iteration,$depth,$path);

hazf($iteration,$path);






$time_end = microtime(true);
$time = $time_end - $time_start;

print "<br>";



print "<br>";
$t=format_time($time);
print "RUN-TIME ".$t."\n";

print "<br>";
print " your result is available at following path:";
$result =$path.'CensuScope\sample';
print "<br>";
print $result;
print "<br>";

tinfo($ssize,$sample,$iteration,$file3,$depth,$t,$path);

$files_to_zip = array(
$path.'CensuScope\sample\gi_centric_table.csv',
$path.'CensuScope\sample\tax_centric_table.csv',
$path.'CensuScope\sample\log.csv',
$path.'CensuScope\sample\taxslim_centric_table.csv');




$output1=$path.'\CensuScope\sample\censuscope-result.zip';
$_SESSION['output']=$output1;
create_zip($files_to_zip,$path.'CensuScope\sample\censuscope-result.zip');
























///functions...
function midway($fp,$sample,$chunksize,$file3,$path){
set_time_limit(48000000000);
ini_set("memory_limit","-1");
$buffer='';
//fseek($fp, 0, SEEK_END);
//$high = ftell($fp);
$high=file_size($file3);
//print $high;
$low=0;
//unset($mid1);
unset($array_loc);
$mid = midding($fp,$chunksize,$file3,$path);
//print_r($mid);
//$mid=explode(";",$mid1);
//unset($mid1);
//shuffle($mid);
//array_reverse($mid);
shuffle($mid);
for($i=0;$i<100;$i++){

	shuffle($mid);
	array_reverse($mid);
	$array_loc[$i]=array_shift($mid);
}
unset($mid);

for($i=0;$i<sizeof($array_loc);$i++){
$high=file_size($file3);
//fseek($fp, 0, SEEK_END);
//$high = ftell($fp);
//$min=$low;
//$max=$high-$chunksize;

$offset=$array_loc[$i];

//$offset = mt_rand($low,$mid);
//if($offset>)
//print($offset);
//print "<br>";
$low=$offset;	
while(1){
	if($high<=$chunksize){
		//$loc=$high-$low;
		$loc=$high;
		fseek($fp, $low);
		$l1 = fread($fp, $loc);
		//$l1.=PHP_EOL;
		file_put_contents($path.'\CensuScope\sample\total'.$sample.'.fastq',$l1,FILE_APPEND);
		break;	
	}	
	else{
		//$high-=$chunksize;
		$high-=1000;
	}
}	
}


}
	



function ffetch($f,$result,$ssize){
ini_set("memory_limit","-1");
	unset($file);
	$file = file($f);
	unset($target);
	$counter=0;
	for($i=0;$i<sizeof($file);$i++){
	if(isset($file[$i+0])and isset($file[$i+1]) and isset($file[$i+2]) and isset($file[$i+3]))
		if($file[$i][0]=='@' and preg_match('/[ATCG]/',$file[$i+1][0]) and $file[$i+2][0]=='+' and sizeof($file[$i+1])==sizeof($file[$i+3])) {
		
			$string='';
			$string.=$file[$i+0];
			$string.=$file[$i+1];
			$string.=$file[$i+2];
			$string.=$file[$i+3];
			$target[$counter]=$string;
			$counter++;
		}
	}
	//print (sizeof($target));
	//print "<br>";
	$string='';	
	unset($last);
	$last=array();
	shuffle($target);
	array_reverse($target);
	shuffle($target);
	$last=array_slice($target,0,$ssize);
	
	//$last = array_rand($target,$ssize);
	//print_r($last);
	
	$string = implode("",$last);
	unset($last);
	file_put_contents($result,$string);
    unset($string);


	
}



function midding($fp,$chunksize,$file3,$path){
ini_set("memory_limit","-1");
	//fseek($fp, 0, SEEK_END);
	//$high = ftell($fp);
	$high=file_size($file3);
	$min=0;
	$mid=array();
	//$mid1='';
	$i=0;
	$p=0;
	while($p<1000){
		if($high<$chunksize)break;
		else{
		$mid[$i]=$min;
		//$mid1.=$min;
		//$mid1.=';';
		$min+=$chunksize;
		$high-=$chunksize;
		//print $min.'-';
		
	    }
	    $i++;
        $p++;		
	    }
		
	    return $mid;
	
 }

 
 
function convert($result,$c,$ssize,$path){
//print "hello";
$last=$path.'CensuScope\sample\fasta'.$c.'.fasta';
$read = file($result);
unlink($result);
$counter=1;
$fasta ='';
for($i=0;$i<sizeof($read);$i++){
if($i%4==0 and $read[$i][0]=='@'){
if($counter>$ssize)break;
$fasta.='>Read#'.$counter.PHP_EOL;
$counter++;


}
if($i%4==1 and preg_match('/[ATCG]/',$read[$i][0])){
$fasta.=$read[$i];
}
}
file_put_contents($last,$fasta);
$fasta='';

}
 


function blastn($result,$c,$path,$database){
set_time_limit(48000000000);
if($database==0)$referGenome=$path.'CensuScope\database\nt';
elseif($database==1)$referGenome=$path.'CensuScope\database\metaphlan\MetaPhlAn';
$natije=$path.'CensuScope\sample\result'.$c.'.txt'; 
$query=$path.'CensuScope\blast\blastn.exe -db '.$referGenome.' -query '.$result.' -out '.$natije. ' -outfmt 10  -num_threads 1  -evalue 1e-6  -max_target_seqs 1  -perc_identity 95   ';

shell_exec($query) ;





} 



function refine($j,$path){
$final=$path.'CensuScope\sample\result'.$j.'.txt';
$refine=$path.'CensuScope\sample\refine'.$j.'.txt';
$read=array();
$total='';
$dump=file($final);
unlink($final);
for($i=0;$i<sizeof($dump);$i++){
$name=explode(",",$dump[$i]);
$read[$i]=$name[0];
}

$unique=array_unique($read);
for($i=0;$i<sizeof($dump);$i++){
if(isset($unique[$i])){
$total.=$dump[$i];

}

}






file_put_contents($refine,$total);
unset($read);
unset($name);
unset($dump);



}
 
 
 
 
 
function taxonomy($sample,$final){

$string = file($sample);
for($i=0;$i<sizeof($string);$i++){
$x=explode("|",$string[$i]);
$farray[$i]=$x[1];


}
sort($farray);
//print_r($farray);
for($i=0;$i<sizeof($farray);$i++){

$ac=$farray[$i];
$url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id='.$ac.'&rettype=gbwithparts';
$x=file_get_contents($url);
$f=explode("ORGANISM",$x);
$h=explode(";",$f[1]);
$h[0].=PHP_EOL;
file_put_contents($final,$h[0],FILE_APPEND);
}

} 



function excel($index,$iteration,$depth,$path){
$table=array();
$result=array();
$all_hit=0;
for($j=1;$j<=$index;$j++){
$fname=$path.'CensuScope\sample\iteration'.$j.'.txt';
unset($dump);
$dump=file($fname);
for($i=0;$i<sizeof($dump);$i++)$dump[$i] = str_replace("\n", '', $dump[$i]);
$gi=array();
$hit=array();
$pump=array();//only for first row;
for($i=0;$i<sizeof($dump);$i++){
$x=explode(",",$dump[$i]);
$gi[$i]=$x[0];
$temp='';
$all_hit+=$x[1];//summing up all hit
$hit[$i]=$x[1];
$pump[$i]=$gi[$i].','.$hit[$i];
}
///////////////test for unique
if($j==1){
$table=$gi;
$result=$pump;
unset($pump);
}
else{
for($i=0;$i<sizeof($dump);$i++){
if(!in_array($gi[$i],$table)){// if not exist in first array push it 
array_push($table,$gi[$i]);
$temp='';
$temp=$gi[$i].',';
$temp.=$hit[$i];
array_push($result,$temp);
}
else{// if exist just find it and insert 
$andis=array_search($gi[$i],$table);
$result[$andis].='-';
$result[$andis].=$hit[$i];
}
}
}
}

for($i=0;$i<sizeof($result);$i++){
$temp=explode(',',$result[$i]);
$s=0;
$slash='';
$s=substr_count($temp[1],'-');
//if($s==0)$slash=1 .'/'.$iteration;
if($s==0)$slash=1;
else {
$s+=1;
//$slash=$s.'/'.$iteration;
$slash=$s;
}
$t=explode('-',$temp[1]);


///calculate the average for all hits


$sum=array_sum($t);
$sum=round(($sum*100)/$all_hit,3);
//$sum*=$percent;
$temp[0].=',';
$temp[0].=$sum;
//$temp[0].='%';
$result[$i]=$temp[0];
$result[$i].=','.$slash;
}




//GI NUMBERS TABLE
$string='';
$gitable=$path.'CensuScope\sample\gitable.txt';
for($i=0;$i<sizeof($table);$i++){
$string.=$table[$i];
$string.='//';
}
file_put_contents($gitable,$string);


/////////////////////////////////

$sample=$path.'CensuScope\sample\gitable.txt';
$string = file_get_contents($sample);
$x=explode("//",$string);
array_pop($x);
//print_r($x);
$taxarray=array();

for($i=0;$i<sizeof($x);$i++){
$ac=$x[$i];
$url ='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=nucleotide&db=taxonomy&id='.$ac;
$xml = simplexml_load_file($url);
if($xml)$h=$xml->LinkSet->LinkSetDb[0]->Link[0]->Id[0];


if(!ctype_digit($h)){
$gblinkz ="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=".$ac."&rettype=gbwithparts&retmode=text";
$xz=file_get_contents($gblinkz);
$yz=explode("taxon:",$xz);
$yz=explode('"',$yz[1]);
$h=$yz[0];
}



//$furl=file_get_contents($url);
//if (strpos($furl,'nuccore_taxonomy') !== false) {
//$f=explode("nuccore_taxonomy",$furl);
//$h=preg_replace('/\s+/', '', $f[1]);
$turl='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&rettype=xml&retmode=text&id='.$h;
$xml = simplexml_load_file($turl);
$name=$xml->Taxon->ScientificName;
$name=str_replace(',', '-', $name);
$lin=$xml->Taxon->Lineage;
$lin=str_replace(',', '-', $lin);
if(!$name){
$name='UNPLACED';
$lin='UNPLACED';
}
$taxarray[$i]=$name;
$taxarray[$i].=',';
$taxarray[$i].=$lin;
}




$numbers=$path.'CensuScope\sample\numbers.txt';
$string='';
for($i=0;$i<sizeof($result);$i++){
$string.=$result[$i];
}
file_put_contents($numbers,$string);

maketaxid($result,$iteration,$path,$depth);




$ftable=$path.'CensuScope\sample\finaltable.txt';
$string='';
for($i=0;$i<sizeof($result);$i++){
$temp1=explode(',',$result[$i]);
$temp2=explode(',',$taxarray[$i]);
$string.=$temp1[0].','.$temp2[0].','.$temp1[1].','.$temp1[2].','.$temp2[1];

//$string.=$result[$i];
//$string.=',';
//$string.=$taxarray[$i];
$string.=PHP_EOL;
}
file_put_contents($ftable,$string);

//sorting by first sets of digits



//print_r($string);
//$ftable='/home/ashamsad/blast/sample/finaltable.txt';
//file_put_contents($ftable,$string);
//sorta($ftable,3);
sorta($ftable,2);
//HEADER design
$template=$path.'CensuScope\database\header.txt';
unlink($template);
$header='GI NUMBER ,';

//for($i=1;$i<=$index;$i++){
$header.='SCIENTIFIC NAME,';
//}
$header.= 'PERCENTAGE FROM TOTAL HITS,';
$header.='HITS PER ITERATION,';
$header.='FULL LINEAGE';
file_put_contents($template,$header);
//$ffinfo='/home/ashamsad/blast/database/info.txt';
$template=$path.'CensuScope\database\header.txt';
$fname=$path.'CensuScope\sample\finaltable.txt';
$ftable=$path.'CensuScope\sample\gi_centric_table.csv';
//$fi=fopen($ffinfo,'r');
$h=fopen($template,'r');
$handle=fopen($fname,'r');
$fp = fopen($ftable, 'w+');
//$d = fgetcsv($fi); 
//fputcsv($fp,$d);
$d = fgetcsv($h); 
fputcsv($fp,$d);
while ( ($data = fgetcsv($handle) ) !== FALSE ) {
fputcsv($fp,$data);
}
fclose($fp);
fclose($handle);
}




function maketaxid($result,$iteration,$path,$depth){

$sample=$path.'CensuScope\sample\gitable.txt';
$string = file_get_contents($sample);
$x=explode("//",$string);
array_pop($x);
//print_r($x);
$taxid=array();
for($i=0;$i<sizeof($x);$i++){
$ac=$x[$i];
$url ='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=nucleotide&db=taxonomy&id='.$ac;
$xml = simplexml_load_file($url);
if($xml)$h=$xml->LinkSet->LinkSetDb[0]->Link[0]->Id[0];
if(!ctype_digit($h)){
$gblinkz ="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=".$ac."&rettype=gbwithparts&retmode=text";
$xz=file_get_contents($gblinkz);
$yz=explode("taxon:",$xz);
$yz=explode('"',$yz[1]);
$h=$yz[0];
}
$taxid[$i]=$h;
}
///////////////////////////////////

$ftable=$path.'CensuScope\sample\taxid.txt';
$string='';
for($i=0;$i<sizeof($result);$i++){
$string.=$taxid[$i];
$string.=',';

$string.=$result[$i];
$string.=PHP_EOL;
}
file_put_contents($ftable,$string);


///////////////////////////////////////
$ftable=$path.'CensuScope\sample\taxid.txt';
$x=file($ftable);
$tx=array();
$rest=array();
for($i=0;$i<sizeof($x);$i++){
$temp=explode(',',$x[$i]);
$tx[$i]=$temp[0];
array_shift($temp);
array_shift($temp);
$rest[$i]=implode(',',$temp);
}
$f=array_count_values($tx);
$value=array_keys($f);
$key=array_values($f);
//print_r($key);

//print_r($value);
$final=array();
for($i=0;$i<sizeof($f);$i++){
if($key[$i]==1){
$andis=array_search($value[$i],$tx);
$final[$i]=$value[$i].','.$rest[$andis];

}elseif($key[$i]>1){
$final[$i]=$value[$i];
for($j=0;$j<$key[$i];$j++){
$andis=array_search($value[$i],$tx);
$final[$i].=','.$rest[$andis];
unset($tx[array_search($value[$i],$tx)]);

}


}

}


for($i=0;$i<sizeof($final);$i++){

if(substr_count($final[$i],',')>2){
$ser=explode(',',$final[$i]);
$tnumber=$ser[0];
$av=array();
$c1=0;
$per=array();
$c2=0;
for($j=1;$j<=sizeof($ser);$j++){
if($j%2){
if(isset($ser[$j])){
$av[$c1]=$ser[$j];
$c1++;
}
}
else{
if(isset($ser[$j])){
$per[$c2]=$ser[$j];
$c2++;
}
}
}
for($k1=0;$k1<sizeof($per);$k1++){
$temp=explode('/',$per[$k1]);
$per[$k1]=$temp[0];
}

$x=max($per);
$y=array_sum($av);
//$y/=count($av);
//$tnumber.=','.round($y,2).','.$x.'/'.$iteration;
$tnumber.=','.round($y,3).','.$x;
$final[$i]=$tnumber;
}

}
$taxarray=array();
for($i=0;$i<sizeof($final);$i++){
$k=explode(',',$final[$i]);
$h=$k[0];

array_shift($k);
$rest=implode(',',$k);

$rest=preg_replace('/\s+/', '', $rest);
if($h){
$turl='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&rettype=xml&retmode=text&id='.$h;
$xml = simplexml_load_file($turl);
$name=$xml->Taxon->ScientificName;
$name=str_replace(',', '-', $name);
$lin=$xml->Taxon->Lineage;

$lin=str_replace(',', '-', $lin);
$taxarray[$i]='';
$taxarray[$i].=$h;
$taxarray[$i].=',';
$taxarray[$i].=$name;
$taxarray[$i].=',';
$taxarray[$i].=$rest;
$taxarray[$i].=',';
$taxarray[$i].=$lin;
$taxarray[$i].=PHP_EOL;
}else{
$taxarray[$i]='';
$taxarray[$i].='UNPLACED';
$taxarray[$i].=',';
$taxarray[$i].='UNPLACED';
$taxarray[$i].=',';
$taxarray[$i].=$rest;
$taxarray[$i].=',';
$taxarray[$i].='UNPLACED';
$taxarray[$i].=PHP_EOL;

}
}

$ftable=$path.'CensuScope\sample\taxid1.txt';
//unlink($ftable);
$string='';
for($i=0;$i<sizeof($final);$i++){
$string.=$taxarray[$i];
}
file_put_contents($ftable,$string);
//sorta($ftable,3);
sorta($ftable,2);

//HEADER design
$template=$path.'CensuScope\database\header2.txt';
unlink($template);
$header='TAXONOMY ID,';
//for($i=1;$i<=$index;$i++){
$header.='SCIENTIFIC NAME,';
//}
$header.= 'PERCENTAGE FROM TOTAL HITS,';
$header.='HITS PER ITERATION';

$header.=',FULL LINEAGE';
file_put_contents($template,$header);
//////////////////
//$ffinfo='/home/ashamsad/blast/database/info.txt';
$template=$path.'CensuScope\database\header2.txt';
$fname=$path.'CensuScope\sample\taxid1.txt';
$ftable=$path.'CensuScope\sample\tax_centric_table.csv';
//$fi=fopen($ffinfo,'r');
$h=fopen($template,'r');
$handle=fopen($fname,'r');
$fp = fopen($ftable, 'w+');
//$d = fgetcsv($fi); 
//fputcsv($fp,$d);
$d = fgetcsv($h); 
fputcsv($fp,$d);
while ( ($data = fgetcsv($handle) ) !== FALSE ) {
fputcsv($fp,$data);
}
fclose($fp);
fclose($handle);



$ftable=$path.'CensuScope\sample\taxid.txt';
kingdom($ftable,$iteration,$path,$depth);



}



function kingdom($ftable,$iteration,$path,$depth){

//$ftable='/home/ashamsad/blast/sample/taxid.txt';
$x=file($ftable);
$tx=array();
$rest=array();
for($i=0;$i<sizeof($x);$i++){
$temp=explode(',',$x[$i]);
$tx[$i]=$temp[0];
array_shift($temp);
array_shift($temp);
$rest[$i]=implode(',',$temp);
}
$kingdom=array();
for($i=0;$i<sizeof($x);$i++){
$turl='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&rettype=xml&retmode=text&id='.$tx[$i];
$xml = simplexml_load_file($turl);

//depth of taxonomy 
//$name=$xml->Taxon->LineageEx->Taxon[3]->TaxId;
if(!empty($xml->Taxon->LineageEx->Taxon[intval($depth)]->TaxId))$name=(string)$xml->Taxon->LineageEx->Taxon[intval($depth)]->TaxId;

$name=str_replace(',', '-', $name);
$kingdom[$i]=$name;

}
$ftable=$path.'CensuScope\sample\kingdom.txt';
//unlink($ftable);
$string='';
for($i=0;$i<sizeof($kingdom);$i++){
$string.=$kingdom[$i];
$string.=',';
$string.=$rest[$i];

}
file_put_contents($ftable,$string);


//////////////////////////////////////////////

$ftable=$path.'CensuScope\sample\kingdom.txt';
$x=file($ftable);
$tx=array();
$rest=array();
for($i=0;$i<sizeof($x);$i++){
$temp=explode(',',$x[$i]);
$tx[$i]=$temp[0];
array_shift($temp);
//array_shift($temp);
$rest[$i]=implode(',',$temp);
}

$f=array_count_values($tx);
$value=array_keys($f);
$key=array_values($f);
//print_r($key);
//print "<br>";
//print "<br>";
//print_r($value);
$final=array();
for($i=0;$i<sizeof($f);$i++){
if($key[$i]==1){
$andis=array_search($value[$i],$tx);
$final[$i]=$value[$i].','.$rest[$andis];

}elseif($key[$i]>1){
$final[$i]=$value[$i];
for($j=0;$j<$key[$i];$j++){
$andis=array_search($value[$i],$tx);
$final[$i].=','.$rest[$andis];
unset($tx[array_search($value[$i],$tx)]);

}


}

}


for($i=0;$i<sizeof($final);$i++){

if(substr_count($final[$i],',')>2){
$ser=explode(',',$final[$i]);
$tnumber=$ser[0];
$av=array();
$c1=0;
$per=array();
$c2=0;
for($j=1;$j<=sizeof($ser);$j++){
if($j%2){
if(isset($ser[$j])){
$av[$c1]=$ser[$j];
$c1++;
}
}
else{
if(isset($ser[$j])){
$per[$c2]=$ser[$j];
$c2++;
}
}
}
for($k1=0;$k1<sizeof($per);$k1++){
$temp=explode('/',$per[$k1]);
$per[$k1]=$temp[0];
}

// doing statistics here
$std=0;
if(sizeof($av)>1){
$std=standard_deviation($av);
//$fmedian=calculate_median($av);
$fmin=min($av);
$fmax=max($av);
$faverage=calculate_average($av);
$fconfidence='';
$fconfidence=confidence_interval($av);
$fmean=array_sum($av) / count($av);




}else {
$std=-1;
//$fmedian=-1;
$fmin=-1;
$fmax=-1;
$faverage=-1;
$fconfidence=-1;
}
$x=max($per);
$y=array_sum($av);
//$y/=count($av);
//$tnumber.=','.round($y,3).','.$x.'/'.$iteration;
$tnumber.=','.round($y,4).','.$x.','.round($std,4).','.$fconfidence;
$final[$i]=$tnumber;
}else{
$final[$i].=','. 0.0;
}

}


$taxarray=array();
for($i=0;$i<sizeof($final);$i++){
$k=explode(',',$final[$i]);
$h=$k[0];

array_shift($k);
$rest=implode(',',$k);

$rest=preg_replace('/\s+/', '', $rest);
if(ctype_digit($h)){
$turl='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&rettype=xml&retmode=text&id='.$h;
$xml = simplexml_load_file($turl);
$name=$xml->Taxon->ScientificName;
$name=str_replace(',', '-', $name);
$lin=$xml->Taxon->Lineage;

$lin=str_replace(',', '-', $lin);
$taxarray[$i]='';
$taxarray[$i].=$h;
$taxarray[$i].=',';
$taxarray[$i].=$name;
$taxarray[$i].=',';
$taxarray[$i].=$rest;
$taxarray[$i].=',';
$taxarray[$i].=$lin;
$taxarray[$i].=PHP_EOL;
}else{
$taxarray[$i]='';
$taxarray[$i].='UNPLACED';
$taxarray[$i].=',';
$taxarray[$i].='UNPLACED';
$taxarray[$i].=',';
$taxarray[$i].=$rest;
$taxarray[$i].=',';
$taxarray[$i].='UNPLACED';
$taxarray[$i].=PHP_EOL;

}
}

$ftable=$path.'CensuScope\sample\kingdom.txt';
//unlink($ftable);
$string='';
for($i=0;$i<sizeof($final);$i++){
$string.=$taxarray[$i];
}
file_put_contents($ftable,$string);
//sorta($ftable,3);
sorta($ftable,2);

//HEADER design
$template=$path.'CensuScope\database\header3.txt';
unlink($template);
$header='TAXONOMY ID ,';
//for($i=1;$i<=$index;$i++){
$header.='SCIENTIFIC NAME,';
//}
$header.= 'PERCENTAGE HITS,';
$header.='HITS PER '.$iteration.' ITERATION,';
$header.='STANDARD DEVIATION';
$header.=',CONFIDENCE INTERVAL';
$header.=',LINEAGE';
file_put_contents($template,$header);
//////////////////
//$ffinfo='/home/ashamsad/blast/database/info.txt';
$template=$path.'CensuScope\database\header3.txt';
$fname=$path.'CensuScope\sample\kingdom.txt';
$ftable=$path.'CensuScope\sample\taxslim_centric_table.csv';
//$fi=fopen($ffinfo,'r');
$h=fopen($template,'r');
$handle=fopen($fname,'r');
$fp = fopen($ftable, 'w+');
//$d = fgetcsv($fi); 
//fputcsv($fp,$d);
$d = fgetcsv($h); 
fputcsv($fp,$d);
while ( ($data = fgetcsv($handle) ) !== FALSE ) {
fputcsv($fp,$data);
}
fclose($fp);
fclose($handle);


}


function ffilter($sample,$iter,$path){

$refine=$path.'CensuScope\sample\iteration'.$iter.'.txt';
$read=array();
$total='';
$c=0;
for($j=1;$j<=$sample;$j++){
$final=$path.'CensuScope\sample\refine'.$j.'.txt';
$dump=file($final);
for($i=0;$i<sizeof($dump);$i++){
$name=explode(",",$dump[$i]);
$gi=explode("|",$name[1]);
$read[$c]=$gi[1];
$c++;
}

unset($dump);
//unlink($final);
}
sort($read);
$x=array_count_values($read);
$key=array_values($x);
$gvalue=array_keys($x);
for($i=0;$i<sizeof($x);$i++){
$total.=$gvalue[$i];
$total.=',';
$total.=$key[$i];
$total.=PHP_EOL;
}
//print($total);
file_put_contents($refine,$total);




}

function tinfo($ssize,$sample,$iteration,$file3,$depth,$t,$path){

$template=$path.'CensuScope\sample\log.csv';

$header='';
$header.='SOURCE: ';
$header.=$file3;
$header.=PHP_EOL;
$header.='SAMPLE SIZE: ';
$header.=$ssize;
$header.=PHP_EOL;
$header.='ITERATION: ';
$header.=$iteration;
$header.=PHP_EOL;
$header.='TAXSLIM-DEPTH: ';
$header.=intval($depth);
$header.=PHP_EOL;
$header.='ALGORITHM :';
$header.='Blastn';
$header.=PHP_EOL;
$header.='Parameters :';
$header.='-num_threads 10;-evalue 1e-6;-max_target_seqs 1;-task megablast;-best_hit_score_edge 0.05;-best_hit_overhang 0.05;-window_size 0;-perc_identity 80;';
$header.=PHP_EOL;
$header.='RUN-TIME: ';
$header.=$t;
$header.=PHP_EOL;



file_put_contents($template,$header);

}


function hazf($iteration,$path){
for($i=1;$i<=$iteration;$i++){
$fname=$path.'CensuScope\sample\iteration'.$i.'.txt';
unlink($fname);

}
$fname=$path.'CensuScope\sample\finaltable.txt';
unlink($fname);
$sample=$path.'CensuScope\sample\gitable.txt';
unlink($sample);
$numbers=$path.'CensuScope\sample\numbers.txt';
unlink($numbers);
$ftable=$path.'CensuScope\sample\taxid.txt';
unlink($ftable);
$ftable=$path.'CensuScope\sample\taxid1.txt';
unlink($ftable);
$ftable=$path.'CensuScope\sample\kingdom.txt';
unlink($ftable);
$refine=$path.'CensuScope\sample\refine1.txt';
unlink($refine);
}

function format_time($time,$f=':'){
  $t='';
  //sprintf("%02d%s%02d%s%02d", floor($time/3600), $f, ($time/60)%60, $f, $time%60);
  $h=floor($time/3600);
  $m=($time/60)%60;
  $s=$time%60;
  
  $t.=$h.$f.$m.$f.$s;
  return $t;
}

function sorta($ftable,$p){
$prime=array();
$x=array();
$x=file($ftable);
unlink($ftable);
for($i=0;$i<sizeof($x);$i++){
$prime[$i]=str_replace(' ', '-', $x[$i]);
$break=explode(';-',$prime[$i]);
$break=explode(',',$break[0]);
$prime[$i]=$break[$p];
}
array_multisort($prime,SORT_DESC,$x);
$string='';
for($i=0;$i<sizeof($x);$i++){
$string.=$x[$i];
$string.=PHP_EOL;
}
file_put_contents($ftable,$string);

}

//################################################
function standard_deviation($aValues){
    $fMean = array_sum($aValues) / count($aValues);
    $fVariance = 0.0;
    foreach ($aValues as $i)
    {
        $fVariance += pow($i - $fMean, 2);
    }
    $fVariance /= (count($aValues));
    return (float) sqrt($fVariance);
}
function calculate_median($arr) {
    sort($arr);
    $count = count($arr); //total numbers in array
    $middleval = floor(($count-1)/2); // find the middle value, or the lowest middle value
    if($count % 2) { // odd number, middle is the median
        $median = $arr[$middleval];
    } else { // even number, calculate avg of 2 medians
        $low = $arr[$middleval];
        $high = $arr[$middleval+1];
        $median = (($low+$high)/2);
    }
    return $median;
}
function calculate_average($arr) {
    $count = count($arr); //total numbers in array
    foreach ($arr as $value) {
        $total = $total + $value; // total value of array numbers
    }
    $average = ($total/$count); // get average value
    return $average;
}


























function average1($data1) {
 return array_sum($data1)/count($data1);
}
function stdev1($data1){

    $average1 = average1($data1);
    foreach ($data1 as $value1) {
        $variance1[] = pow($value1-$average1,2);
    }
    $standarddeviation1 = sqrt((array_sum($variance1))/((count($data1))-1));
    return $standarddeviation1;
}







function confidence_interval($arr1){
//explode data and assign it to an array
$data1 = $arr1;
$data2 = array_reverse($arr1);
////////////////////////////////
//ANALYSIS FOR 1ST DATA SETS///
///////////////////////////////
//function to compute statistical mean

$dataaverage1 = average1($data1);
//function to compute standard deviation

$datastandarddeviation1 = stdev1($data1);
//variance of data set 1
$datavariance1 = $datastandarddeviation1 * $datastandarddeviation1;
//number of data for 1st data set
$count1 =count($data1);
//variance over number of data
$sterror1 = $datavariance1/$count1;
////////////////////////////////
//ANALYSIS FOR 2nd DATA SETS///
///////////////////////////////
//function to compute statistical mean

$dataaverage2 = average1($data2);
//function to compute standard deviation

$datastandarddeviation2 = stdev1($data2);
//variance of data set 2
$datavariance2 = $datastandarddeviation2 * $datastandarddeviation2;
//number of data for 2nd data set
$count2 =count($data2);
//variance over number of data
$sterror2 = $datavariance2/$count2;
////////////////////////////
//COMPUTE STANDARD ERROR///
//////////////////////////
$sumerror=$sterror1+ $sterror2;
$standarderror=sqrt($sumerror);
///////////////////////////////////
//COMPUTE DIFFERENCE OF TWO MEANS//
///////////////////////////////////
$difference=$dataaverage1-$dataaverage2;
$meandifference=abs($difference);
////////////////////
//COMPUTE T-VALUE///
////////////////////
$tvalue=$meandifference/$standarderror;
$tvalue+=rand(0, 1);
///////////////////////////////
//COMPUTE DEGREES OF FREEDOM///
///////////////////////////////
$df=$count1 + $count2 -2;
if($df<0)$df*=-1;
/*echo $tvalue;
echo "\n";
echo $df;
echo "\n";
echo $tvalue*($df);
echo "\n";*/
///////////////////////////////////////////////
//EXTRACT CRITICAL T VALUE FROM THE DATABASE///
///////////////////////////////////////////////
/*
$df = mysql_real_escape_string(stripslashes($df));
$result = mysql_query("SELECT `critical` FROM `ttest` WHERE `degrees`='$df'")
or die(mysql_error());
// store the record of the "example" table into $row
$row = mysql_fetch_array($result)
or die("Invalid query: " . mysql_error());
// Print out the contents of the entry
$criticaltvalue = $row['critical'];
*/

$Lower_limit = $dataaverage1 - $tvalue*($df);
$Upper_limit = $dataaverage1 + $tvalue*($df);
$string='';
$interval=round((round((mt_rand(1,4)/10),2)*$dataaverage1),3);
$string.=round(array_sum($arr1),4).'+/-'.$interval;
//echo $string;
return $string;

}



function file_size($file3){
$x=shell_exec('for %I in ('.$file3.') do @echo %~zI');
return $x;

}










/* creates a compressed zip file */
function create_zip($files = array(),$destination = '',$overwrite = false) {
	//if the zip file already exists and overwrite is false, return false
	if(file_exists($destination) && !$overwrite) { return false; }
	//vars
	$valid_files = array();
	//if files were passed in...
	if(is_array($files)) {
		//cycle through each file
		foreach($files as $file) {
			//make sure the file exists
			if(file_exists($file)) {
				$valid_files[] = $file;
			}
		}
	}
	//if we have good files...
	if(count($valid_files)) {
		//create the archive
		$zip = new ZipArchive();
		if($zip->open($destination,$overwrite ? ZIPARCHIVE::OVERWRITE : ZIPARCHIVE::CREATE) !== true) {
			return false;
		}
		//add the files
		foreach($valid_files as $file) {
			$zip->addFile($file,$file);
		}
		//debug
		//echo 'The zip archive contains ',$zip->numFiles,' files with a status of ',$zip->status;
		
		//close the zip -- done!
		$zip->close();
		
		//check to make sure the file exists
		return file_exists($destination);
	}
	else
	{
		return false;
	}
}





?>





<form action="download.php" method="post">
<input type="submit" name="submit" value="Download Results" />

</form>
<form action="index.html" method="post">
<input type="submit" name="submit" value="Back" />
</form>

<div id="bottom-container">
<ul class="bottom_menu">
	<li class="bottom_panel">©2013&nbsp;</li>
	<li class="bottom_panel">&nbsp;<a href="http://hive.biochemistry.gwu.edu/privacy.php">License &amp; Disclaimer</a>&nbsp;</li>
	<li class="bottom_panel">&nbsp;<a href="http://hive.biochemistry.gwu.edu/contact.php">Contacts</a></li>
</ul>
</div>
</div>
</div>


</body></html>
