
/******************************************************
*
* Sequence data manipulation routines
*
******************************************************/
	
var gSeq_Parsing="";
var gSeq_dirListDest="";

function vSeq_compiledVioseq(container, txt)
{
	alert(txt+" reads were read from sequence file.");
	gSeq_Parsing="";
	vDir_listPath(container,"","vDir_listDirContent",1);
	
}

function vSeq_fastaInfo(seqfile, prfx) 
{
    
    if (seqfile.indexOf("--")==0)seqfile=cookieGet("vSeq_selected_"+seqfile.substring(2));
    
	var ccmd=protectFields('-verbose 0 -wrap 60 -cnt 100 -print len=1 -fSeq '+prfx+seqfile+' 0 128 ');
	var t="";
	t+="<table class='QP_tbl' style='position:relative; left:-100px; background-color:#FFFFFF;' width='100%'>";
		t+="<tr><th style='border:1px dotted #4282B1;' width='100%'><img border=0 height=16 width=48  src='img/dna.gif'>"+seqfile+"<img border=0 height=16 width=48  src='img/dna.gif'><a style='float:right;' href='#' onclick='javascript:vis(\"floatDiv\",\"sectHid\")'>&times;</a></th></tr>";
		t+="<tr><td style='border:1px dotted #4282B1;' width='100%'><div style='overflow: auto; height: 200px; width: 100%; padding: 0px;' id='preFastaInfo' >fasta</div></td></tr>"
	t+="</table>";
	
    gObjectSet("floatDiv",gMoX,gMoY,t,"show","-","-");
    
    gObject("floatDiv").className="sectVis";
	 
	linkCmd("viotools&raw=1&exec="+ccmd,"preFastaInfo","-");
	setTimeout("vis(\"floatDiv\",\"sectHid\")",10000);
}

function vSeq_dirListItemClicked(dirtxt,container, callback, isdir)
{
	var inf=dirtxt.split(":");
	var dir=inf[0];

	if(!isdir){
		
		if(dir.indexOf(".vioseq")!=-1) {
			var ls=document.forms[gVDir_formName].elements[gSeq_dirListDest].value.split("; ");
			var isin=0, allbut="";
			for ( var li=0 ; li<ls.length; ++li ){ 
				if(ls[li]==dir )isin=1; // this field was in the list
				else {
					if(allbut.length>0)allbut+="; ";
					allbut+=ls[li];
				}
			}
			if(isin) document.forms[gVDir_formName].elements[gSeq_dirListDest].value=allbut;
			else {
				if(allbut.length>0)allbut+="; ";
				allbut+=dir;
				document.forms[gVDir_formName].elements[gSeq_dirListDest].value=allbut;
			}
			cookieSet("vSeq_selected_"+gSeq_dirListDest,allbut);
			return ;
		}
				
		if(gSeq_Parsing.length) {
			alert("the file "+gSeq_Parsing+" is being parsed now\nPlease wait for it to finish");
			return; 
		}
		var rval=confirm("The file "+dir+" has not been parsed yet\nCompilation may take sime time\nDo you want to compile it now?");
		if(!rval)return ;
		gSeq_Parsing=dir;
        linkCmd("viotools&raw=1&exec="+protectFields("-verbose 0 -fParse %QUERY%"+dir),container,vSeq_compiledVioseq);
	}
	if(isdir)linkCmd("dirList&raw=1&path="+dir, container, callback);

}

function vSeq_size(idim) 
{
	var SZ="";
	if(idim>=10000){idim=idim/1000; SZ="K";}
	if(idim>=10000){idim/=1000; SZ="M";}
	if(idim>=10000){idim/=1000; SZ="G";}
	idim=parseInt(idim);
	if((""+idim).length>=4)idim=parseInt(idim/1000)+","+(idim+"").substring(1);
	idim+=SZ;
	return idim;
}

function vSeq_dirListItemText(isdir, itmtxt, txt, curdir)
{
	var inf=itmtxt.split(":");
	var itm=inf[0];
    var idim=vSeq_size((inf.length>1) ? parseInt(inf[1]) : 0);
	var sdim=(inf.length>1) ? "&nbsp;&nbsp;&nbsp;<small>["+idim+"]<img border=0 height=12 width=24 src='img/dna.gif'></small>" : "";
		
	if(isdir)return "-";
	if(itm.indexOf(".vioseq")!=-1){
        //var ccmd=protectFields('-verbose 0 -cnt 100 -print len=1 -fSeq %QUERY%'+curdir+itm);
        //sdim="&nbsp;<a href=\"javascript:linkSelf('viotools&raw=1&exec="+ccmd+"','new');\" >"+sdim+"</a>";
        var idim=parseInt(sdim);
        
        sdim="&nbsp;<a href=\"#\" onclick=\"javascript:vSeq_fastaInfo('"+curdir+itm+"','%QUERY%');\" >"+sdim+"</a>";
        return "<img border=0 src='img/ok.gif' height=12 >&nbsp;"+itm + sdim;
    }
	
	var extpos=itm.lastIndexOf(".");
	var fnd=(extpos!=-1) ? itm.substring(0,extpos+1) : "";
	if(extpos!=-1){
		var isfound= txt.indexOf(fnd+"vioseq")==-1 ? 0 : 1 ;
		if(!isfound) return "<img border=0 src='img/process.gif' height=12 >&nbsp;"+itm;
	}
	return "";//<img border=0 src='ok.gif' height=12 >&nbsp;"+fnd+"vioseq";
}




function vSeq_onChangeQrySub(e)
{
	if(!e)e=event;
		
	var container=e.srcElement.name;
	cookieSet("vSeq_selected_"+container,e.srcElement.value);
}
function vSeq_loadedAvailableFiles(container, txt)
{

	var vrr=txt.split("\n");
	var defval=document.forms[gVDir_formName].elements[container].value;

	var arrt=vrr[0].split("|");
	    
	var selt="<table><tr><td>";
    selt+="<select class='inputEditable' name='"+container+"' onchange='vSeq_onChangeQrySub()' >";
	for ( var im=0; im<arrt.length; ++im) {
		var inf=arrt[im].split(":");
		var flnm=inf[0];
		var dim= (inf.length>1) ? "  // "+vSeq_size(inf[1])+"" : "";
		selt+="<option value='"+flnm+"' "+((defval==flnm) ? "selected" : "") +">"+flnm+dim+"</option>";
	}
	selt+="</select>";
    selt+="</td><td>";
    if(flnm.indexOf("vioseq")!=-1)selt+="<a href=\"javascript:vSeq_fastaInfo('--subject','%SUBJECT%');\" ><img border=0 height=12 width=24 src='img/dna.gif'></a>";
    selt+="</td></tr></table>";
	gObject(container+"_layer").innerHTML=selt;
	
}


