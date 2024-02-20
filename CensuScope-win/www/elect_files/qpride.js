//external functions
	//function QPride_refreshRequest()
		///function QPride_check(container, txt) 
	//function QPride_trackDataBlobs(dsections, szlimit)
	//function QPride_backgroundExecution(cmd, progressbar, callback)
	//function QPride_downloadBlob(blbname,filename, container, callback )

var req;
	
	var QPride_statList=new Array ("Any","Waiting","Processing","Running","Suspended","Done","Killed","Program Error","System Error","Unknown");
	var QPride_knownFormatList =  ",.csv,.mat,.txt,.html,.doc,.jpg,.gif,.bmp,.xls,.ppt,.out,.fa,.fasta,.fastq,.cpp,...";
	var QPride_hideFormatList = ",.tbl,-out.csv,...";
	var QPride_trackDataList=",errors,console,form,$summary.txt,...";
	
//	var QPride_delayFirstCheck=10;
	var QPride_delayCheck=10000;
	var QPride_delayCheckBG=1000;
	var QPride_DoneFunc="";
	var QPride_DoneJumpDelay=30000;
	var QPride_lastForm="";
	var QPride_downloadedForm="";
	var QPride_checkFunc="";
	var QPride_downloadedDataNamesFunc=QPride_downloadedDataNames;
	var QPride_dataNamesList=new Array();
	
	var QPride_dataActionFunctions=new Array();
	QPride_dataActionFunctions.push( {name:".csv", func :"QPride_showTable", icon: "Show Table"} );
	//QPride_dataActionFunctions.push( {name:".csv", func :"QPride_showGraphFunc", icon: "Graph"} );
	QPride_dataActionFunctions.push( {name:".mat", func :"QPride_showTable", icon: "eye"} );
	  
		
			
		
	// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
	// _/
	// _/ Reuest Status Management
	// _/
	// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
	function QPride_refreshRequest()
	{
		linkCmd("-qpCheck&raw=1&req="+req+"&svc="+docLocValue("svc"),0,QPride_check);
	}
	function QPride_check(container, txt) 
	{
		var ar=txt.split(",");
		var svcTitle=ar[0];
		var reqName=ar[1];
		req=parseInt(ar[2]);
		var stat=parseInt(ar[3]);
		var time=parseInt(ar[4]);
		var progress=parseInt(ar[5]);
		var progress100=parseInt(ar[6]);
		var grpCnt=parseInt(ar[7]);
		
		QPride_showReqStatus(reqName, req,stat,time,progress, progress100, grpCnt);// show the progress
        
		QPride_getDataNames();
		QPride_trackDataBlobs();
		QPride_trackReqInfo();
		
		if(QPride_checkFunc) QPride_checkFunc(reqName, req,stat,time,progress, progress100,grpCnt);
		
		if(QPride_delayCheck && stat<4) {
			setTimeout("QPride_refreshRequest()", QPride_delayCheck);
		}
		
		if(stat>=4 && QPride_DoneFunc && QPride_DoneFunc!=""){
			QPride_delayCheck=0;
			setTimeout(QPride_DoneFunc+"("+req+","+stat+")",QPride_DoneJumpDelay);
		}
	} 

	   
	//
	// this function retrieves information on the status of requests
	//
	function QPride_showReqStatus(QPride_reqName, QPride_reqID, QPride_stat, QPride_timespan, QPride_progress, QPride_progress100 )
	{
			
		var o;
		v=gObject("QP_reqName");if(v)v.innerHTML=QPride_reqName;
		v=gObject("QP_reqID");if(v)v.innerHTML=QPride_reqID;
		v=gObject("QP_progress");if(v)v.innerHTML=QPride_progress;
		v=gObject("QP_progress100");if(v)v.innerHTML=QPride_progress100;
		v=gObject("QP_timespan");if(v){
			var tt=QPride_timespan;
			var ts="";
			if(tt>24*3600){ts+=parseInt(tt/(24*3600))+"/"; tt=parseInt(tt%(24*3600));}
			{ts+=(100+parseInt(tt/(3600))+"").substring(1)+":"; tt=parseInt(tt%(3600));}
			{ts+=(100+parseInt(tt/(60))+"").substring(1)+":"; tt=parseInt(tt%(60)).toFixed(2);}
			{ts+=(100+parseInt(tt)+"").substring(1)+"";}
			v.innerHTML=ts;//QPride_timespan+" secs";
		}
		v=gObject("QP_stat");if(v){
			var tt="";
			if(QPride_stat>=4 && QPride_DoneFunc)tt+="<a href='javascript:"+QPride_DoneFunc+"("+req+","+QPride_stat+")' >";
			tt+=QPride_statList[QPride_stat];
			if(QPride_stat>=4 && QPride_DoneFunc)tt+="</a>";
			v.innerHTML=tt;
		}
		v=gObject("QP_progressBar");if(v) {
			var psh = cookieSet('progVis');
			var t="";
			t+=QPride_formProgress( 100, "", QPride_progress , QPride_progress100);
			v.innerHTML=t;
		}
	}    

	function QPride_formProgress( width, hdr, prog , prog100, locreq )
	{
		var t="<table class='QP_progress' width='"+width+"%'><tr>";
                t+="<td bgcolor='#4282B1' align='right' width='"+prog100+"%' ><font color=#ffffff>";	
				if(prog100>=50){t+=prog+"("+prog100+"%)"; if(locreq)t+="&nbsp;<small><small>"+locreq+"</small></small>";}
				t+="</font></td><td bgcolor=#ffffff align=left width="+(100-prog100)+"%><font color='#4282B1'>";
				if(prog100<50){t+=prog+"("+prog100+"%)"; if(locreq)t+="&nbsp;<small><small>"+locreq+"</small></small>";}
				t+="</font></td>";
				t+="</tr></table>";
		return t;
	}
	function QPride_killRequest(lreq)
	{
		if(!lreq)lreq=req;
		linkSelf("-qpKillReq&req="+lreq);
		
	}

	// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
	// _/
	// _/ Request Submission on Background
	// _/
	// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
		 
	 
	var QPride_gProgSectContent=new Array();
    var QPride_gProgParams=new Array();
	function QPride_backgroundCheckRequest(sparams, txt) // we use container here as a function name  
	{
        //alert("rrr:"+txt+"\n\n\n"+sparams);
        //alert(txt);
        var params=JSON.parse(sparams);

        var callback=params.callback;
		var progressbar=params.progressbar;
		
		if(!txt || txt.length==0){eval(callback+"(0,0)"); return ;}
		var ar=txt.split(",");
		var svcTitle=ar[0];
		var reqName=ar[1];
		rrreq=parseInt(ar[2]);
		var stat=parseInt(ar[3]);
		var time=parseInt(ar[4]);
		var progress=parseInt(ar[5]);
		var progress100=parseInt(ar[6]);
		
		if(progressbar && progressbar.length!=0)gObject(progressbar).innerHTML=QPride_formProgress( 100, "", progress ,progress100 , rrreq );
		if(stat>=4){
        
        	if(progressbar && progressbar.length!=0)gObject(progressbar).innerHTML=QPride_gProgSectContent[progressbar]; // restore the contentr
            if(!params.namefetch || params.namefetch.length==0 ) 
                eval(callback+"("+rrreq+","+stat+", "+params.xtraparams+")");
            else {
            
                if(callback=="download")QPride_downloadBlob(params.namefetch);
                else linkCmd("-qpData&raw=1&default=error:%20"+rrreq+"%20"+params.namefetch+"%20not%20found&req="+rrreq+"&dname="+params.namefetch,params.xtraparams,eval(callback));
            }
		}
		else if(QPride_delayCheckBG) {
			setTimeout("linkCmd('-qpCheck&raw=1&req="+rrreq+"','"+sparams+"',QPride_backgroundCheckRequest)", QPride_delayCheckBG);
		}
	}

	function QPride_backgroundExecution(cmd, progressbar, callback, namefetch, xtraparams )
	{	
        var params = { 'progressbar': progressbar, 'callback': callback, 'namefetch' : namefetch , 'xtraparams' : xtraparams };
        if(progressbar && progressbar.length!=0)QPride_gProgSectContent[progressbar]=gObject(progressbar).innerHTML; // remember the old content of the section
        
        linkCmd(cmd+"&raw=1",JSON.stringify(params),QPride_backgroundCheckRequest);
	}

			
// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
// _/
// _/ Data management
// _/
// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/

	function QPride_formDataNamesTable(dd, showengin)
	{
		//var dd=availdata.split(/[\s,]+/);
		var tshow="",thide="";
		
		for ( var i=0 ; i< dd.length; ++i){ if(dd[i].length<2)break;
			
		// determine the file extension
			var extpos=dd[i].lastIndexOf(".");
			var ext = (extpos!=-1) ? dd[i].substring(extpos) : "";
			
			// see if this is a known or to-be-hidden format
			if(QPride_hideFormatList.indexOf(","+ext+",")!=-1)continue;
			
			// make table rows 
			var tt="<tr><td style='padding:5px;' width='55%'>"+dd[i]+"</td>";
			// this is always downloadable
			tt+="<td style='padding:5px;' width='15%'><a href='javascript:QPride_downloadBlob(\"$"+dd[i]+"\")' >Download</a></td>";
			for( var ifun=0; ifun<QPride_dataActionFunctions.length; ++ifun) {
				var act=QPride_dataActionFunctions[ifun];
				if(act.name!=ext)continue;
				tt+="<td style='padding:5px;' width='15%'><a href='javascript:"+act.func+"(\""+dd[i]+"\")' >"+act.icon+"</td>";
			}
			tt+="</tr>";
			
			if(QPride_knownFormatList.indexOf(","+ext+",")!=-1)tshow+=tt; // this is a known format
			else thide+=tt;
					
		}
		
		var container= "eng"+Math.random();
		var t="<table width='100%'>";
		t+="<tbody id='"+container+"' class='sectVis'>";
		t+=tshow;
		t+="</tbody>";
		if(showengin && thide.length) {
			t+="<tr><td style='padding:5px;'>"+ovis(container+".qpride","sectHid","more...|less...")+"&nbsp;</td></tr>";
			t+="<tbody id='"+container+".qpride' class='sectHid'>";
			t+=thide;
			t+="</tbody>";
		}	
		t+="</table>";
		
		return t;
	}	
	function QPride_findDataName( dname )
	{
		for( var i=0; i<QPride_dataNamesList.length; ++i) { 
			if(QPride_dataNamesList[i]==dname)return i+1;
		}
		return 0;
	}
	function QPride_downloadedDataNames(container, txt)
	{
		QPride_dataNamesList=txt.split(/[\s,]+/);
		var o=gObject(container);
		if(o)o.innerHTML=QPride_formDataNamesTable(QPride_dataNamesList, false);	
	}
	
	function QPride_getDataNames(container, lreq)
	{
		if(!container)container="QP_data";
	
		linkCmd("-qpDataNames&raw=1&req="+(lreq ? lreq : req),container,QPride_downloadedDataNamesFunc);
	}
	
	// shows all predefined data blobs in HTML
	function QPride_trackDataBlobs(dsections, szlimit)
	{
		if(!dsections)dsections=QPride_trackDataList;
	    var sds=dsections.split(",");
		for( var i=0; i<sds.length; ++i) {
			var isgrp=(sds[i].substring(0,1)=="$") ? true : false;
			var dnam=((sds[i].substring(0,1)=="$") || (sds[i].substring(0,1)=="#") ) ? sds[i].substring(1) : sds[i];
			var o=gObject("QP_"+dnam)
			if(o) {
				if(dnam=="form")linkCmd("-form&raw=1&req="+req,sds[i],QPride_downloadedFormContent);
				else linkCmd("-qpData&dname="+dnam+"&dsize="+(szlimit ? szlimit : 2048)+"&req="+req+(isgrp ? "&grp=1" :""),sds[i],QPride_downloadedDataSection);	
			}
		}
	}
	
	// shows the content of the form
	function QPride_downloadedFormContent(container, txt)
	{
		QPride_lastForm=txt;
		var o=gObject("QP_"+container);if(!o)return;
		if(!txt || txt.length==0) {o.className="sectHid";return;}
		
		var ar=QPride_lastForm.split("\n");
		var t="<table width='100%'>";
		for ( var ir=0; ir<ar.length - 1; ++ir ){
			var cls=ar[ir].split("=");
			t+="<tr><td width='60%'><b>"+cls[0]+"</b></td><td width='40%'><pre>"
			for ( var ic=1; ic<cls.length; ++ic)t+=cls[1];
			t+="</pre></td></tr>";
		}
		t+="</table>";
		o.innerHTML=t;
		if(QPride_downloadedForm!=""){
			eval(QPride_downloadedForm);
		}
	}

	// shows the content inside of the similarly named span
	function QPride_downloadedDataSection(container, txt)
    {
		var t="";
		var istbl=0;
		if(container.substring(0,1)=="$" || container.substring(0,1)=="#" ){
			t+="<table width='100%'><tr><td>";
			istbl=1;
			container=container.substring(1);
		}
		var o=gObject("QP_"+container);
		if(!txt || txt.length==0) o.className="sectHid";
		t+="<pre>"+txt+"</pre></td></tr>";
		if(istbl)t+="</table>";
		o.innerHTML=t;
	}

	function QPride_downloadBlob(blbname,filename, container, callback )
	{
		var url;
		
		if(blbname=="all"){
			var cmd="-req "+req+" -dataGetAll /tmp 1 ";
			url="-qpSubmit&svc=qapp&exec="+protectFields(cmd);
			blbname="QPData-"+req+".tar.gz";
		}
		else if(filename){
			url="-qpFile&raw=1&file="+filename;
		}
		else if(blbname) { 
			var isgrp=0;
			if(blbname.substring(0,1)=="$"){blbname=blbname.substring(1);isgrp=1;}
			url="-qpData&req="+req+"&dname="+blbname;
			if(isgrp)url+="&grp=1";
		}
		
		if(!container){ // direct link download
			linkSelf(url);
			return ;
		}
			
		var cmd="-req "+req+" -dataGetAll /tmp 1 ";
		var url="-qpSubmit&svc=qapp&exec="+protectFields(cmd);
		QPride_backgroundExecution(url, container ? container : "QP_progress",(callback ? callback : "QPride_downloadBlob")+"(0,\""+blbname+"\");nullFunc");
	}
	

	
// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
// _/
// _/ Request and Job Info Management
// _/
// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
	function QPride_downloadedRequestInfo(container, txt)
	{
		var o=gObject(container); if(!o)return;
		if(!txt || txt.length==0){ o.className="sectHid"; return ;}
		
		var ar=txt.split("\n");
		var t="<table width='100%'>";
		for ( var ir=0; ir<ar.length; ++ir ){
			var cls=ar[ir].split("//");if(cls.length<2)continue;
			
			t+="<tr>";
			t+="<td width='10%'><pre>"+cls[0]+"</pre></td>";
			t+="<td width='45%'><pre>"+cls[2]+"</pre></td>";
			t+="<td width='45%'><pre>";
			for ( var ic=3; ic<cls.length; ++ic)t+=cls[ic];
			t+="</pre></td>";
			t+="</tr>";
		}
		t+="</table>";
		
		o.innerHTML=t;
	}
	function QPride_trackReqInfo()
	{
		var container="QP_reqInfo";
		var o=gObject(container); if(!o)return;
		linkCmd("-qpReqInfo&req="+req,container,QPride_downloadedRequestInfo);	
	}
	
// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
// _/
// _/ Final Request Submission on Background
		// _/
// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
	
	function QPride_showTable(dname)
	{
		var url="tbl.cgi?cmd=tblqry&req="+req;
		cookieSet("QPride_selectedTable",dname);
		window.open(url,"Show Graph");
	}
		

// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
// _/
// _/ Request management
// _/
// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/

function QPride_reqaction(isgrp, reqid,act)
{
	linkCmd("req="+req+"&cmd=-"+(isgrp ? "grp" : "req")+"SetAction&action="+act);
}
	    
		
function QPride_formValue(varnm, qpform)
{
	if(!qpform)qpform=QPride_lastForm;
	
	var ppos=qpform.indexOf(varnm+" = "); if(ppos==-1)return "";
	var retv=qpform.substring(ppos+varnm.length+3);
	var epos=retv.indexOf("\n");if(epos==-1)return retv;
	return retv.substring(0,epos);
}
		
// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/
// _/
// _/ Service management
// _/
// _/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/_/

		
		var QPride_svcList;
		var QPride_svcCols=25;
	    var QPride_svcRows=0;
		var QPride_categList = new Array();
		
		var QPride_svcParamHeaders= new Array ( "svcID","name","title","isUp","svcType","knockoutSec","maxJobs","nice","sleepTime","maxLoops","parallelJobs","delayLaunchSec","politeExitTimeoutSec","maxTrials","restartSec","priority","cleanUpDays","runInMT","noGrabDisconnect","cmdLine","hosts","emails","categories","maxmemSoft","maxmemHard");
		
		var QPride_cfgList;
		var QPride_cfgCols=2;
		var QPride_cfgRows=0;
		
		