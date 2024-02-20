We have chosen to apply the Creative Commons Attribution-NonCommercial-NoDerivs 
(http://creativecommons.org/licenses/by-nd/3.0/) License to all parts of this software.
Mazumder Lab.

Authors: Amir Shams, Pan Yang, Vahan Simonyan, Raja Mazumder

censuscope v1.2 (UNIX version) README
=====================================
Contact: amir.shams84@gmail.com, mazumder@gwu.edu

What is censuscope?
------------------------
* censuscope is designed and optimized for the quick detection the components of a given NGS metagenomic data and providing users
  with a standard format report of components into species or higher taxonomic node resolution.

  The core of the censuscope consists of census-based reads file generation and blast/bowtie based short-reads alignment. 
  censuscope is capable of sample contamination evaluation, microbiome components detection and other meta-omic
  related data analysis.
  
  
Installation instructions: 
-----------------------------------------------------------------------
<<you have to have censuscope Package before Running censuscope>>
censuscope Package Link : http://hive.biochemistry.gwu.edu/data.php

* you have to have contatanated BLAST-NT database as reference, we have already prepared 
   this database. When the the download has finished (it is a zip folder with 11.0 GB size containg all required file)
   extract the compressed Package (CensuCcope.zip) into your system.
   The compressed folder includes BLAST-NT database (17GB) and Blastn software and two 
   read datasets from virus and prokaryotes (virus.fastq and prok.fastq) for testing.
   


How to use censuscope?
---------------------------
* you need to have PHP or ZEND server on your system for running this version   
<< It is recommended that you use a computer with RAM capacity more than 1GB>>
<<this version is optimized for lower than 20 Cores CPU>>

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
  