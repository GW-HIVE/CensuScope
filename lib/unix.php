<?php
error_reporting(0);
   $options = getopt("i:s:d:t:p:"); 
    if (!is_array($options) ) { 
        print "There was a problem reading in the options.\n\n"; 
        exit(1); 
    } 
    $errors = array();
    
    print "ITERATION : ".$options['i']."\n";
    print "READ-SIZE : ".$options['s']."\n";
    print "TAXSLIM_DEPTH : ".$options['t']."\n";
    print "SOURCE DIRECTORY : ".$options['d']."\n";
    print "PACKAGE PATH : ".$options['p']."\n";
    
    
$time_start = microtime(true);

set_time_limit(48000000000);
ini_set("memory_limit","-1");

if($options['d'] && file_exists($options['d'])){//file3 is our sample file 
$file3 = $options['d'];

}elseif(!$options['d'] || !file_exists($options['d'])){

 print("Fatal Error: you did not select the source file or the path is incorrect \n");
 die();
 }



//$file3=$options['d'];
//$file3='/home/ashamsad/blast/source/test.fastq';
$ssize=$options['s'];
//$ssize=2000;//based on your request
//$sample=$options['r'];
$sample =1;
$iteration=$options['i'];



//$iteration=4;
$depth=$options['t'];


if($options['p'] && file_exists($options['p'].'CensuScope/blast/blastdb_aliastool')){//pack is nt package 
$path = $options['p'];
}elseif(!$options['p']|| !file_exists($options['p'].'CensuScope/blast/blastdb_aliastool')){

 print("Fatal Error: you did not select the package or the path is incorrect \n ");
die();
}
//$path=$options['p'];

/*
$name_extension=explode('/',$file3);
$name_extension1=explode('.',end($name_extension));
$name_extension2=$path.'CensuScope/sample/'.$name_extension1[0].rand(1,1000);
echo $name_extension2;
mkdir($name_extension2), 0777);
*/
if(file_exists($path.'CensuScope/sample/gi_centric_table.csv')){ unlink($path.'CensuScope/sample/gi_centric_table.csv');}
if(file_exists($path.'CensuScope/sample/log.csv')){ unlink($path.'CensuScope/sample/log.csv');}
if(file_exists($path.'CensuScope/sample/tax_centric_table.csv')){unlink($path.'CensuScope/sample/tax_centric_table.csv');}
if(file_exists($path.'CensuScope/sample/taxslim_centric_table.csv')){unlink($path.'CensuScope/sample/taxslim_centric_table.csv');}
for($i=1;$i<=100;$i++){
$fname=$path.'CensuScope/sample/iteration'.$i.'.txt';
unlink($fname);

}


//iteration
$klo=1;
for($it=1;$it<=$iteration;$it++){
print $it.'-';
$fp = fopen($file3,'r') or die('Couldnot get handle');
fseek($fp, 0, SEEK_END);
$high = ftell($fp);

$line_of_file='wc -l '.$file3;
$high=shell_exec($line_of_file);

if($ssize<intval($high)){
//echo "goodbuy";
//creating random sample
for($i=1;$i<=$sample;$i++){

$query=$path.'CensuScope/blast/Random '.$file3.' '.$ssize.' '.$path.'CensuScope/sample/sample'.$i.'.fastq'; 
shell_exec($query);
}
/*
if($ssize<$high){

//echo "goodbuy";
//setting chunk size
$p=floor($high/1000);
//print ($p);
$chunksize=$p;//based on the size of read

//random picking
for($i=1;$i<=$sample;$i++){
midway($fp,$i,$chunksize,$path);
}
fclose($fp);

//ffetch
for($i=1;$i<=$sample;$i++){
$f =$path.'CensuScope/sample/total'.$i.'.fastq';
$result =$path.'CensuScope/sample/sample'.$i.'.fastq';
ffetch($f,$result,$ssize);
unlink($f);	
}


} */
}
else if($ssize>=intval($high)){

//echo "hello";
$srcfile=$file3;
$dstfile=$path.'CensuScope/sample/sample1.fastq';
mkdir(dirname($dstfile), 0777, true);
copy($srcfile, $dstfile);

}



//      fastq to fasta converter
for($i=1;$i<=$sample;$i++){
$result =$path.'CensuScope/sample/sample'.$i.'.fastq';
convert($result,$i,$ssize,$path);
}


// running blastn
for($i=1;$i<=$sample;$i++){
$result =$path.'CensuScope/sample/fasta'.$i.'.fasta';
blastn($result,$i,$path,$klo);
//unlink($result);
refine($i,$path);
$klo++;

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
print "\nDONE\n";
$t=format_time($time);
print "Estimated Processing Time ".$t."\n";
tinfo($ssize,$sample,$iteration,$file3,$depth,$t,$path);



///functions...
function midway($fp,$sample,$chunksize,$path){
set_time_limit(48000000000);
ini_set("memory_limit","-1");
 



$buffer='';
fseek($fp, 0, SEEK_END);
$high = ftell($fp);
$low=0;
//unset($mid1);
unset($array_loc);
$mid = midding($fp,$chunksize);
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

fseek($fp, 0, SEEK_END);
$high = ftell($fp);
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
		file_put_contents($path.'CensuScope/sample/total'.$sample.'.fastq',$l1,FILE_APPEND);
		break;	
	}	
	else{
		//$high-=$chunksize;
		$high-=1000;
	}
}	
}


}
//################################################	



function ffetch($f,$result,$ssize){
	unset($file);
	$file = file($f);
	unset($target);
	$counter=0;
	for($i=0;$i<sizeof($file);$i++){
	if(isset($file[$i+0])and isset($file[$i+1]) and isset($file[$i+2]) and isset($file[$i+3]))
		if($file[$i][0]=='@' and preg_match('/[ATCGNatcgn]/',$file[$i+1][0]) and $file[$i+2][0]=='+' and sizeof($file[$i+1])==sizeof($file[$i+3])) {
		
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
//################################################


function midding($fp,$chunksize){
	fseek($fp, 0, SEEK_END);
	$high = ftell($fp);
	$min=0;
	$mid=array();
	//$mid1='';
	$i=0;
	while(1){
		if($high<$chunksize)break;
		else{
		$mid[$i]=$min;
		//$mid1.=$min;
		//$mid1.=';';
		$min+=$chunksize;
		$high-=$chunksize;
	    }
	    $i++;	
	    }
		
	    return $mid;
	
 }

 //################################################
 
function convert($result,$c,$ssize,$path){
//print "hello";
$last=$path.'CensuScope/sample/fasta'.$c.'.fasta';
$read = file($result);
//unlink($result);
$counter=1;
$fasta ='';
for($i=0;$i<sizeof($read);$i++){
if($i%4==0 and $read[$i][0]=='@'){
if($counter>$ssize)break;
$fasta.='>Read#'.$counter.PHP_EOL;
$counter++;


}
if($i%4==1 and preg_match('/[ATCGNatcgn]/',$read[$i][0])){
$fasta.=$read[$i];
}
}
file_put_contents($last,$fasta);
$fasta='';

}
 
//################################################

function blastn($result,$c,$path,$klo){
set_time_limit(48000000000);
ini_set("memory_limit","-1");
$natije=$path.'CensuScope/sample/result'.$c.'.txt';
$file_klo= $path.'CensuScope/sample/blast_iteration'.$klo.'.txt';
$query=$path.'CensuScope/blast/blastn -db '.$path.'CensuScope/database/nt -query '.$result.' -out '.$natije. ' -outfmt 10  -num_threads 10  -evalue 1e-6  -max_target_seqs 1  -perc_identity 80   ';
//$query=$path.'CensuScope/blast/blastn -db '.$path.'CensuScope/database/nt -query '.$result.' -out '.$file_klo. ' -outfmt 0  -num_threads 10  -evalue 1e-4   -perc_identity 75   ';

//print $query;
//print "\n";
//$query=$path.'CensuScope/blast/blastn -db '.$path.'CensuScope/database/nt -query '.$result.' -out '.$natije. ' -outfmt 10  -num_threads 100  -evalue 1e-4  -max_target_seqs 1 -task megablast -perc_identity 50 ';

shell_exec($query) ;





}

//################################################

function refine($j,$path){
$final=$path.'CensuScope/sample/result'.$j.'.txt';
$refine=$path.'CensuScope/sample/refine'.$j.'.txt';
$read=array();
$total='';
$dump=file($final);
//unlink($final);
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
 
 //################################################
 
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


//################################################
function excel($index,$iteration,$depth,$path){

$table=array();
$result=array();
$all_hit=0;
for($j=1;$j<=$index;$j++){
$fname=$path.'CensuScope/sample/iteration'.$j.'.txt';
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
$all_hit=1;
//$sum=round(($sum*100)/$all_hit,4);
$sum=round(($sum)/$all_hit,4);
//$sum*=$percent;
$temp[0].=',';
$temp[0].=$sum;
//$temp[0].='%';
$result[$i]=$temp[0];
$result[$i].=','.$slash;
}




//GI NUMBERS TABLE
$string='';
$gitable=$path.'CensuScope/sample/gitable.txt';
for($i=0;$i<sizeof($table);$i++){
$string.=$table[$i];
$string.='//';
}
file_put_contents($gitable,$string);


/////////////////////////////////

$sample=$path.'CensuScope/sample/gitable.txt';
$string = file_get_contents($sample);
$x=explode("//",$string);
array_pop($x);
//print_r($x);
$taxarray=array();

for($i=0;$i<sizeof($x);$i++){
$ac=$x[$i];
$url ='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=nucleotide&db=taxonomy&id='.$ac;
//echo $url;
//echo "\n";
$xml = simplexml_load_file($url);
//if(file_exists($xml)){
$hip=$xml->LinkSet->LinkSetDb[0]->Link[0]->Id[0];
//echo $hip;
//echo "\n";
//if(file_exists($xml) && ctype_digit($hip)){
$gblinkz ="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=".$ac."&rettype=gbwithparts&retmode=text";
$xz=file_get_contents($gblinkz);
$yz=explode("taxon:",$xz);
$yz=explode('"',$yz[1]);
$h=0;
$h=$yz[0];
//}
//echo $h;
//echo "\n";
//$furl=file_get_contents($url);
//if (strpos($furl,'nuccore_taxonomy') !== false) {
//$f=explode("nuccore_taxonomy",$furl);
//$h=preg_replace('/\s+/', '', $f[1]);
$turl='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&rettype=xml&retmode=text&id='.$h;
//if(file_exists($xml))
$xml = simplexml_load_file($turl);
$name=$xml->Taxon->ScientificName;
$name=str_replace(',', '-', $name);
$lin=$xml->Taxon->Lineage;
$lin=str_replace(',', '-', $lin);
if(empty($name)){
$name='UNPLACED';
$lin='UNPLACED';
}
$taxarray[$i]=$name;
$taxarray[$i].=',';
$taxarray[$i].=$lin;
}




$numbers=$path.'CensuScope/sample/numbers.txt';
$string='';
for($i=0;$i<sizeof($result);$i++){
$string.=$result[$i];
}
file_put_contents($numbers,$string);

maketaxid($result,$iteration,$path,$all_hit,$depth);




$ftable=$path.'CensuScope/sample/finaltable.txt';
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

sorta($ftable,2);
//sorta($ftable,3);
//HEADER design
$template=$path.'CensuScope/database/header.txt';
unlink($template);
$header='GI NUMBER ,';

//for($i=1;$i<=$index;$i++){
$header.='SCIENTIFIC NAME,';
//}
$header.= 'TOTAL HIT,';
$header.='HITS PER '.$iteration.'ITERATION ,';
$header.='FULL LINEAGE';
file_put_contents($template,$header);
//$ffinfo='/home/ashamsad/blast/database/info.txt';
$template=$path.'CensuScope/database/header.txt';
$fname=$path.'CensuScope/sample/finaltable.txt';


$ftable=$path.'CensuScope/sample/gi_centric_table.csv';
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




//################################################
function maketaxid($result,$iteration,$path,$all_hit,$depth){

$sample=$path.'CensuScope/sample/gitable.txt';
$string = file_get_contents($sample);
$x=explode("//",$string);
array_pop($x);
//print_r($x);
$taxid=array();
for($i=0;$i<sizeof($x);$i++){
$ac=$x[$i];
$url ='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=nucleotide&db=taxonomy&id='.$ac;
$xml = simplexml_load_file($url);
if(file_exists($xml))$h=$xml->LinkSet->LinkSetDb[0]->Link[0]->Id[0];
//if(file_exists($xml) && !ctype_digit($h)){
$gblinkz ="http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id=".$ac."&rettype=gbwithparts&retmode=text";
$xz=file_get_contents($gblinkz);
$yz=explode("taxon:",$xz);
$yz=explode('"',$yz[1]);
$h=$yz[0];
//}
if(ctype_digit($h))$taxid[$i]=$h;
}
///////////////////////////////////

$ftable=$path.'CensuScope/sample/taxid.txt';
$string='';
for($i=0;$i<sizeof($result);$i++){
$string.=$taxid[$i];
$string.=',';

$string.=$result[$i];
$string.=PHP_EOL;
}
file_put_contents($ftable,$string);


///////////////////////////////////////
$ftable=$path.'CensuScope/sample/taxid.txt';
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
$av[$c1]=$ser[$j];//////////////////////////////
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


//here we calculate stats for gi centric level



// doing statistics here
$std=0;
if(sizeof($av)>1 && $iteration >1 ){
$std=standard_deviation($av);

$x=max($av);
$z=min($av);

//$faverage=calculate_average($av);
$fconfidence='';
$w=array_sum($av) / count($av);

$conferror=$std/sqrt($w);
if($std>($w*2))$confintval=0.36*$conferror;
else if($std>=($w*1)) $confintval=0.66*$conferror;
else $confintval=1.96*$conferror;
$fconfidence=confidence_interval($av);

}else {
$std=0.0;

$x=$z=$w=max($av);
$std=0.0;
$confintval=0.0;

}
$fconfidence=round($w,2).'+/-'.round($confintval,4);
$y=array_sum($av);
$tnumber.=','.round($y,2).','.$x.','.$z.','.round($w,2).','.round($std,2).','.$fconfidence;
$final[$i]=$tnumber;
}else{
$final[$i].=','. 0.0 .','. 0.0 .','. 0.0 .','. 0.0;

}



}
$taxarray=array();
$jingarray=array();
for($i=0;$i<sizeof($final);$i++){
$k=explode(',',$final[$i]);
$h=$k[0];

array_shift($k);
$pjing=array();
$pjing=$k;
array_pop($pjing);
///////////////////////////////
for($pix=0;$pix<sizeof($pjing);$pix++){
$pjing[$pix]=ceil(($pjing[$pix]*$all_hit)/100.0);

}
///////////////////////////////
$jingrest=implode(',',$pjing);








$rest=implode(',',$k);

$rest=preg_replace('/\s+/', '', $rest);
$jingrest=preg_replace('/\s+/', '', $jingrest);
if($h){
$turl='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&rettype=xml&retmode=text&id='.$h;
$xml = simplexml_load_file($turl);
$name=$xml->Taxon->ScientificName;
$name=str_replace(',', '-', $name);
$lin=$xml->Taxon->Lineage;
$lin=str_replace(',', '-', $lin);
$taxarray[$i]='';
$jingarray[$i]='';
$taxarray[$i].=$h;
$jingarray[$i].=$h;
$jingarray[$i].=',';
$taxarray[$i].=',';
$taxarray[$i].=$name;
$taxarray[$i].=',';
$taxarray[$i].=$rest;
$jingarray[$i].=$jingrest;
$taxarray[$i].=',';
$taxarray[$i].=$lin;
$taxarray[$i].=PHP_EOL;
$jingarray[$i].=PHP_EOL;
}else{
$taxarray[$i]='';
$taxarray[$i].='Not Assigned';
$taxarray[$i].=',';
$taxarray[$i].='Not Assigned';
$taxarray[$i].=',';
$taxarray[$i].=$rest;
$taxarray[$i].=',';
$taxarray[$i].='Not Assigned';
$taxarray[$i].=PHP_EOL;
$jingarray[$i]='';
$jingarray[$i].='Not Assigned';
$jingarray[$i].=',';
$jingarray[$i].=$jingrest;
$jingarray[$i].=PHP_EOL;

}
}

$ftable=$path.'CensuScope/sample/taxid1.txt';

$jing=$path.'CensuScope/sample/jing.csv';
//unlink($ftable);
$string='';
$jingstring='taxid,cnt,';
$jingstring.=PHP_EOL;
for($i=0;$i<sizeof($final);$i++){
$string.=$taxarray[$i];
$jingstring.=$jingarray[$i];
}
file_put_contents($ftable,$string);

//file_put_contents($jing,$jingstring);
sorta($ftable,2);
//sorta($ftable,3);
//sorta($ftable,3);
//sorta($jing,1);

//HEADER design
$template=$path.'CensuScope/database/header2.txt';
unlink($template);
$header='TAXONOMY ID,';
//for($i=1;$i<=$index;$i++){
$header.='SCIENTIFIC NAME,';
//}
$header.= 'TOTAL HIT,';
$header.='MAX,';
$header.='MIN,';
$header.='MEAN,';
$header.='STANDARD DEVIATION';
$header.=',CONFIDENCE INTERVAL';
$header.=', FULL LINEAGE';
file_put_contents($template,$header);
//////////////////
//$ffinfo='/home/ashamsad/blast/database/info.txt';
$template=$path.'CensuScope/database/header2.txt';
$fname=$path.'CensuScope/sample/taxid1.txt';
$ftable=$path.'CensuScope/sample/tax_centric_table.csv';
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



$ftable=$path.'CensuScope/sample/taxid.txt';

kingdom($ftable,$iteration,$path,$depth);



}

//################################################

function kingdom($ftable,$iteration,$path,$depth){
//echo "here is the depth  ";
//echo $depth;
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

if($turl){
$xml = simplexml_load_file($turl);
//print_r($xml);
//depth of taxonomy 
//if(!empty($xml->Taxon->LineageEx->Taxon[3]->TaxId))$name=(string)$xml->Taxon->LineageEx->Taxon[3]->TaxId;
if(!empty($xml->Taxon->LineageEx->Taxon[intval($depth)]->TaxId))$name=(string)$xml->Taxon->LineageEx->Taxon[intval($depth)]->TaxId;
//echo $name;
//echo "\n";
$kingdom[$i]=$name;
}else{
//echo "no tax kingdom was available\n";
$kingdom[$i]=0;
}
}

//print_r($kingdom);
$ftable=$path.'CensuScope/sample/kingdom.txt';
//unlink($ftable);
$string='';
for($i=0;$i<sizeof($kingdom);$i++){
$string.=$kingdom[$i];
$string.=',';
$string.=$rest[$i];

}
file_put_contents($ftable,$string);
//////////////////////////////////////////////
$ftable=$path.'CensuScope/sample/kingdom.txt';
$x=file($ftable);
//print_r($x);
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
if(substr_count($final[$i],',')>2 ){
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
if(sizeof($av)>1 && $iteration >1 ){
$std=standard_deviation($av);

$x=max($av);
$z=min($av);

//$faverage=calculate_average($av);
$fconfidence='';
$w=array_sum($av) / count($av);

$conferror=$std/sqrt($w);
if($std>($w*2))$confintval=0.36*$conferror;
else if($std>=($w*1)) $confintval=0.76*$conferror;
else $confintval=1.96*$conferror;
$fconfidence=confidence_interval($av);

}else {
$std=0.0;

$x=$z=$w=max($av);
$std=0.0;
$confintval=0.0;

}
$fconfidence=round($w,2).'+/-'.round($confintval,4);
$y=array_sum($av);
$tnumber.=','.round($y,2).','.$x.','.$z.','.round($w,2).','.round($std,2).','.$fconfidence;
$final[$i]=$tnumber;
}else{
$final[$i].=','. 0.0 .','. 0.0 .','. 0.0 .','. 0.0;

}

}
//echo "hello again";
//print_r($final);
$taxarray=array();
$h=0;
for($i=0;$i<sizeof($final);$i++){
$k=explode(',',$final[$i]);
$h=$k[0];

array_shift($k);
$rest=implode(',',$k);

$rest=preg_replace('/\s+/', '', $rest);


$turl='http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=taxonomy&rettype=xml&retmode=text&id='.$h;
//echo $turl;
//echo "\n";
if($turl){
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
}
else{
$taxarray[$i]='';
$taxarray[$i].='Not Assigned';
$taxarray[$i].=',';
$taxarray[$i].='Not Assigned';
$taxarray[$i].=',';
$taxarray[$i].=$rest;
$taxarray[$i].=',';
$taxarray[$i].='Not Assigned';
$taxarray[$i].=PHP_EOL;

}
}

$ftable=$path.'CensuScope/sample/kingdom.txt';
//unlink($ftable);
$string='';
for($i=0;$i<sizeof($final);$i++){
$string.=$taxarray[$i];
}
file_put_contents($ftable,$string);
sorta($ftable,2);
//sorta($ftable,3);


//HEADER design
$template=$path.'CensuScope/database/header3.txt';
unlink($template);
$header='TAXONOMY ID ,';
//for($i=1;$i<=$index;$i++){
$header.='SCIENTIFIC NAME,';
//}
$header.= 'TOTAL HIT,';
$header.='MAX,';
$header.='MIN,';
$header.='MEAN,';
$header.='STANDARD DEVIATION';
$header.=',CONFIDENCE INTERVAL';
$header.=',FULL LINEAGE';
file_put_contents($template,$header);
//////////////////
//$ffinfo='/home/ashamsad/blast/database/info.txt';
$template=$path.'CensuScope/database/header3.txt';
$fname=$path.'CensuScope/sample/kingdom.txt';
$ftable=$path.'CensuScope/sample/taxslim_centric_table.csv';
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

//################################################
function ffilter($sample,$iter,$path){

$refine=$path.'CensuScope/sample/iteration'.$iter.'.txt';
$read=array();
$total='';
$c=0;
for($j=1;$j<=$sample;$j++){
$final=$path.'CensuScope/sample/refine'.$j.'.txt';
//$final=$path.'CensuScope/sample/result'.$j.'.txt';
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
//################################################
function tinfo($ssize,$sample,$iteration,$file3,$depth,$t,$path){

$template=$path.'CensuScope/sample/log.csv';

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
$header.='-num_threads 10;-evalue 1e-6;-max_target_seqs 1;-perc_identity 80;';
$header.=PHP_EOL;
$header.='ESTIMATED-TIME: ';
$header.=$t;
$header.=PHP_EOL;



file_put_contents($template,$header);

}
//################################################

function hazf($iteration,$path){
for($i=1;$i<=$iteration;$i++){
$fname=$path.'CensuScope/sample/iteration'.$i.'.txt';
//unlink($fname);

}
$fname=$path.'CensuScope/sample/finaltable.txt';
unlink($fname);
$sample=$path.'CensuScope/sample/gitable.txt';
unlink($sample);
$numbers=$path.'CensuScope/sample/numbers.txt';
unlink($numbers);
$ftable=$path.'CensuScope/sample/taxid.txt';
unlink($ftable);
$ftable=$path.'CensuScope/sample/taxid1.txt';
unlink($ftable);
$ftable=$path.'CensuScope/sample/kingdom.txt';
unlink($ftable);
$refine=$path.'CensuScope/sample/refine1.txt';
//unlink($refine);
}
//################################################
function format_time($time,$f=':'){
  $t='';
  //sprintf("%02d%s%02d%s%02d", floor($time/3600), $f, ($time/60)%60, $f, $time%60);
  $h=floor($time/3600);
  $m=($time/60)%60;
  $s=$time%60;
  
  $t.=$h.$f.$m.$f.$s;
  return $t;
}
//################################################
function sorta($ftable,$p){
$prime=array();
$x=array();
$x=file($ftable);
unlink($ftable);
for($i=0;$i<sizeof($x);$i++){
$prime[$i]=str_replace(' ', '-', $x[$i]);
$break=explode(';-',$prime[$i]);
$break=explode(',',$break[0]);
if(isset($break[$p]))$prime[$i]=$break[$p];
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
function standard_deviation($aValues, $bSample = false)
{
    $fMean = array_sum($aValues) / count($aValues);
    $fVariance = 0.0;
    foreach ($aValues as $i)
    {
        $fVariance += pow($i - $fMean, 2);
    }
    $fVariance /= ( $bSample ? count($aValues) - 1 : count($aValues) );
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
$interval=round((round((mt_rand(1,4)/10),2)*array_sum($arr1)),3);
$string.=round(array_sum($arr1),4).'+/-'.$interval;
//echo $string;
return $string;

}

?>