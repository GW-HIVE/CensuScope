# CensuScope
We have chosen to apply the Creative Commons Attribution 3.0 Unsupported License to this version of the software.

Mazumder Lab.

What is CensuScope?
------------------------
* CensuScope is designed and optimized for the quick detection of the components in a given NGS metagenomic dataset and provides users
  with a standard format report of components into species or higher taxonomic node resolution.

  The core of CensuScope consists of census-based reads file generation and Blast/bowtie based short-reads alignment. 
  CensuScope is capable of sample contamination evaluation, microbiome components detection and other meta-omic related data analysis.
  
Installation instructions: 
-----------------------------------------------------------------------
CensuScope  link: https://hive.biochemistry.gwu.edu/dna.cgi?cmd=censuscope

Users must download the CensuScope package before running.


* You need concatenated BLAST-NT database (or the MetaPhlAn Markers database) as a reference, we have already prepared 
   this database. When the download has finished (it is a zip folder with 11.0 GB size containing all required files)
   extract the compressed Package (censuscope.zip) into your system.(for ex. directory is c:\)
   The compressed folder includes BLAST-NT database (17GB) and Blastn software and a bacterial
   read datasets from prokaryotes (bacteria.fastq) for testing.
   
CensuScope v1.2 (Windows version) README
====================================

How to use CensuScope?
---------------------------
<<It is recommended that you use a computer with RAM capacity more than 1GB>>
<<This version is optimized for lower than 10 Cores CPU>>

  1. go to CensuScope-win directory and Run censuscope.exe
  
  2. Set the path of your source file(for example c:\censuscope\source\bacteria.fastq)
  
  3. Set the path of CensuScope Package where you extracted it,please do not include CensuScope main folder into path  (for example c:\ or d:\desktop\)
  
  4.choose your desired database , you can select the Blast-NT or MetaPhlAn database 
  
  5. Set the number of iterations and set the size of samples 
  
  6. Press submit and wait (please do not minimize the application)
  
  7. The output will be downloadable as a Zip file and you can check the generated output at this direction \CensuScope\sample\

THE OUTPUT
-----------------------------

* Final results are in 4 different files (3 csv and 1 txt)

  1. log.txt --  this text file provides all parameters which have been used to run and generate the result
  
  2. gi_centric_table.csv -- GI_numbers sorted result
    
  3. tax_centric_table.csv  -- TAX_ID Sorted result
   
  4. taxslim_centric_table.csv  --  Kingdom-depth taxonomy sorted result
  
CensuScope v1.2 (UNIX version) README
=====================================

How to use CensuScope:
---------------------------
* Users need a PHP or ZEND server on their system for running this version.   
<< It is recommended that you use a computer with RAM capacity more than 1GB>>
<<this version is optimized for lower than 10 Cores CPU>>

  PARAMETERS :
  -i : set the number of iterations
  
  -s : set the size of samples (per READ) 
  
  -t : set the depth of tax_slim (it is set to 3=kingdom)
  
  -d : path to the source 
  
  -p : path of censuscope Package
  
  
  FOR EXAMPLE :
  $ php censuscope.php -i 10 -s 1000 -t 3 -d '/user/desktop/fungi.fastq' -p '/user/'
    
THE OUTPUT
-----------------------------

* Final result are in 4 different files (3 csv and 1 txt)

  1. log.txt --  this text file provide all parameters which have been used to run and generate the result
  
  2. gi_centric_table.csv -- GI_numbers sorted result
    
  3. tax_centric_table.csv  -- TAX_ID Sorted result
   
  4. taxslim_centric_table.csv  --  Kingdom-depth taxonomy (or whatever taxonomic depth is chosen by user) sorted result
  
