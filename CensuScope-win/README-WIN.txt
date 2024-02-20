We have chosen to apply the Creative Commons Attribution 3.0 Unported License to this version of the software.

Mazumder Lab.

Authors: Amir Shams, Pan Yang, Vahan Simonyan, Raja Mazumder

censuscope v1.2 (Windows version) README
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
censuscope Package Link : https://hive.biochemistry.gwu.edu/tools/censuscope.php

* you have to have contatanated BLAST-NT database as reference, we have already prepared 
   this database. When the the download has finished (it is a zip folder with 11.0 GB size containg all required file)
   extract the compressed Package (censuscope.zip) into your system.
   The compressed folder includes BLAST-NT database (17GB) and Blastn software and two 
   read datasets from virus and prokaryotes (virus.fastq and prok.fastq) for testing.
   

How to use censuscope?
---------------------------
<< It is recommended that you use a computer with RAM capacity more than 1GB>>
<<this version optimized for lower than 10 Cores CPU>>

  1. run censuscope.exe
  
  2. set the path of your source file (for example c:\censuscope\source\virus.fastq)
  
  3. set the path of censuscope Package where you extracted it (for example c:\ or d:\desktop)
     
  4. set the number of iterations and set the size of samples 
  
  4. press submit and wait...
  
  5. the output will be downloadable as a Zip file



THE OUTPUT
-----------------------------

* Final result are in 4 different files (3 csv and 1 txt)

  1. log.txt --  this text file provide all parameters which have been used to run and generate the result
  
  2. gi_centric_table.csv -- GI_numbers sorted result
    
  3. tax_centric_table.csv  -- TAX_ID Sorted result
   
  4. taxslim_centric_table.csv  --  Kingdom-depth taxonomy (or whatever taxonomic depth is chosen by user) sorted result
  