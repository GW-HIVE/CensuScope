
var gHome="/";
var gDebug=0;
//var gCGI="seq.cgi";
var gCGI="";
        
    

/***********************************************
* misc global operations 
***********************************************/

var gMoX=0;
var gMoY=0;
var gPgW=2;
var gPgH=2;
var gPgScrlX=0;
var gPgScrlY=0;
var gMoHookPrc="";
var gMoShowXY=false;
var gMoWheelCallback;
var gKeyShift=0;
var gKeyCtrl=0;
    
function nullFunc()
{

}
function gGetPgParams()
{
    if(document.body){
        gPgW=document.body.clientWidth;
        gPgH=document.body.clientHeight;
    }else {
        gPgW=window.screen.width;
        gPgH=window.screen.height;
    }
    gPgCX=Math.round(gPgW/2);
    gPgCY=Math.round(gPgH/2);

    gMoX=gPgCX;
    gMoY=gPgCY;
}
function gOnMouseMove(e)
{
    if(document.all)
        e=event;
	gKeyShift=( e.shiftKey ) ? 1 : 0 ;
	gKeyCtrl=( e.ctrlKey ) ? 1 : 0 ;
    if(gMoHookPrc!="")gMoHookPrc(gMoX,gMoY);
    if( typeof( e.pageX ) == 'number' ) { 
        gMoX = e.pageX;//+document.body.scrollLeft; 
        gMoY = e.pageY;//+document.body.scrollTop; 
        if(document.body) {
            gPgScrlX=document.body.scrollLeft;gPgScrlY=document.body.scrollTop;
        }
    } else {
        gMoX = e.clientX; gMoY = e.clientY;
            
        if( !( ( window.navigator.userAgent.indexOf( 'Opera' ) + 1 ) || ( window.ScriptEngine && ScriptEngine().indexOf( 'InScript' ) + 1 ) || window.navigator.vendor == 'KDE' ) ) {
            if( document.documentElement && ( document.documentElement.scrollTop || document.documentElement.scrollLeft ) ) {
                gPgScrlX=document.documentElement.scrollLeft;gPgScrlY=document.documentElement.scrollTop;
                gMoX += document.documentElement.scrollLeft; gMoY += document.documentElement.scrollTop;
                
            } else if( document.body && ( document.body.scrollTop || document.body.scrollLeft ) ) {
                gPgScrlX=document.body.scrollLeft;gPgScrlY=document.body.scrollTop;
                gMoX += document.body.scrollLeft; gMoY += document.body.scrollTop;
            }
        }
    }
    
        
    if(gMoShowXY)window.status="x=" + gMoX + "  y=" + gMoY + " sx=" + gPgScrlX + "  sy=" + gPgScrlY;
}
    
function gOnMouseWheel(event)
{
	if(!gMoWheelCallback){
		event.returnValue = true;
		return;
	}
	gKeyShift=( event.shiftKey ) ? 1 : 0 ;
	gKeyCtrl=( event.ctrlKey ) ? 1 : 0 ;
		
    var delta = 0;
    if (!event) /* For IE. */
            event = window.event;
    if (event.wheelDelta) { /* IE/Opera. */
            delta = event.wheelDelta/120;
            /** In Opera 9, delta differs in sign as compared to IE.
             */
            if (window.opera)
                    delta = -delta;
    } else if (event.detail) { /** Mozilla case. */
            /** In Mozilla, sign of delta is different than in IE.
             * Also, delta is multiple of 3.
             */
            delta = -event.detail/3;
    }
    /** If delta is nonzero, handle it.
     * Basically, delta is now positive if wheel was scrolled up,
     * and negative, if wheel was scrolled down.
     */
     var ret=0;
    if (delta)
            ret=gMoWheelCallback(delta);
    /** Prevent default actions caused by mouse wheel.
     * That might be ugly, but we handle scrolls somehow
     * anyway, so don't bother here..
     */
    if (ret && event.preventDefault)
            event.preventDefault();
            
	event.returnValue = ret;
}


  
/***********************************************
* misc layer functions 
***********************************************/
function gObject(objnme)                                
{
    pos=objnme.indexOf("->");
    if(pos!=-1){ /* the layer in other frame */
        doc=objnme.substr(0,pos);
        d=eval(doc);
        objnm=objnme.substr(pos+2);
    }
    else {d=document;doc="document";objnm=objnme;}

    return d.getElementById(objnm);
    
}


function gObjectSet(lrnm,lrx,lry,lrcont,lrvis,lrcx,lrcy)
{
    lr=gObject(lrnm);
    if(lrx!="-" || lry!="-"){
        if(lrx!="-")lr.style.left = lrx;
        if(lry!="-")lr.style.top = lry;
    }

    if(lrcx!="-" && lrcy!="-"){
        lr.style.width = lrcx;
        lr.style.height = lrcy;
    }
    if(lrvis!="-"){
        if(lrvis=="show"){lr.style.visibility = "visible";lr.style.display="";}
        if(lrvis=="hide"){lr.style.visibility = "hidden";lr.style.display="none";}
        if(lrvis=="toggle"){
            if(lr.style.visibility=="visible") {lr.style.visibility = "hidden";lr.style.display="none";}
            else {lr.style.visibility = "visible";lr.style.display="";}
        }
    }
    if(lrcont && lrcont!="-"){
        if(lrcont.indexOf("<s>",0)==0){
            lrfunc=lrcont.substr(3);
            lrcont=eval(lrfunc);
         }
        lr.innerHTML = lrcont;
    
    }    
}

var gObjVis_arr=new Array();
function vis( idlist , toggle0 ) 
{
	var o;
//	alert(idlist + ":"+toggle0);
	if(idlist) {
		var jarr=idlist.split(",");
		for ( var i=0; i<jarr.length; ++i) { 
			var toggle;
			var id=jarr[i];
			o=document.getElementById(id);
			
			//if(o) alert("class for "+id +" is " + o.className );
			if(!toggle0) {
				if(!o) toggle="sectVis";
				else if(o.className=="sectHid") toggle="sectVis";
				else toggle="sectHid"; // if(o.className=="sectHid")
			}else toggle=toggle0;
			gObjVis_arr[id]=toggle;
			if(o)o.className=toggle;
			//alert("toggling "+id+" to " + toggle);
		}
		//return toggle;		
	}
	for (var id in gObjVis_arr ) {
		o=document.getElementById(id);
		if(!o) continue;
		o.className!=gObjVis_arr[id];
	}
}

function ovis(id, defvis, plusminus)
{
	if(!plusminus || plusminus.length==0)
		plusminus="<img border=0 width=20 src='img/plus.gif' />|<img border=0 width=20 src='img/xlose.gif' />"
	var plmn=plusminus.split("|");
	if(!defvis)defvis="sectVis";
	
	var t=	"<span id='"+id+"_vis_open'  class='"+ (defvis=="sectVis" ? "sectHid" : "sectVis") +"'><a href='javascript:vis(\""+id+","+id+"_vis_open,"+id+"_vis_close\");'>"+plmn[0]+"</a></span>"+
			"<span id='"+id+"_vis_close' class='"+ (defvis=="sectVis" ? "sectVis" : "sectHid") +"' ><a href='javascript:vis(\""+id+","+id+"_vis_close,"+id+"_vis_open\");'>"+plmn[1]+"</a></span>";
	return t;
}

var gFloatPermanent=0;
var gFloatButtons=3;
var gFloatTimeout=30000;
var gFloatBGColor="bgcolor=#ffffdf";
var gFloatShiftX=-16;
var gFloatShiftY=-16;
var gFloatLastText="";
var gFloatLastTitle="";
var gFloatTimer=0;
var gFloatOpen=0;
function floatDivOpen(title,text, internal)
{
	//text="here";
	if(gFloatTimer)clearTimeout(gFloatTimer);gFloatTimer=0;
	
	var updatepos=(internal || title==gFloatLastTitle) ? 0 : 1;
	if(internal){text=gFloatLastText;title=gFloatLastTitle;}
	else {gFloatLastText=text;gFloatLastTitle=title;}
	
	if(gFloatButtons){
		var btn1="", btn2="";
		if(gFloatButtons&0x2)btn2+="<a href='javascript:gFloatPermanent=1-gFloatPermanent;floatDivOpen(\"-\",\"-\",1)'><img border=0 width=16 src='img/pin"+(gFloatPermanent ? "down" : "up")+".gif'/></a>&nbsp;"
		if(gFloatButtons&0x1)btn1+="<a href='javascript:floatDivClose()'><img border=0 width=16 src='img/xlose.gif'/></a>";
		if(title.length)text="<table class='floatD'  ><tr border=0><td valign=top align=right>"+btn2+"</td><td><small><b>"+title+"</b></small></td><td valign=top align=right>&nbsp;"+btn1+"</td></tr><tr><td colspan=2>"+text+"</td></tr><table>";
		else text="<table class='floatD'  border=0 "+gFloatBGColor+"><tr><td>"+text+"<td><td valign=top>"+btn+"</td></tr><table>";
	}
	gObjectSet("floatDiv",updatepos==0 ? "-" : (gMoX+gFloatShiftX),updatepos==0 ? "-" : (gMoY+gFloatShiftX),text,"show","-","-");
	
	if(!gFloatPermanent)gFloatTimer=setTimeout("floatDivClose(1)",gFloatTimeout);
}
function floatDivClose(isauto)
{
	if(isauto==1 && gFloatPermanent==1)return;
	gObjectSet("floatDiv","-","-","-","hide","-","-");
	if(gFloatTimer)clearTimeout(gFloatTimer);gFloatTimer=0;
	gFloatOpen=0;
}


/********************************************************
* global visibility manipulation functions 
********************************************************/

var gWaitLoad=0;
function gWait(how, txt )
{
	var v=gObject("waiting");if(!v)return ;
	if(txt) v.innerHTML=txt;
	gWaitLoad+=how;if(gWaitLoad<0)gWaitLoad=0;
	if(gWaitLoad)v.className="sectVis";
	else v.className="sectHid";
}
	


var gObjectClsList=new Array();


// returns the class name for this particular section 
function gObjectClass(sect) 
{
	if( gObjectClsList[sect]=="sectVis")return "sectVis";
	return "sectHid";
}

// sets  the classname for particular section
function gObjectClassToggle(sect, which) 
{
	if( which && which.length!=0 ){
		gObjectClsList[sect]=which;
		return ;
	}
		
	var o=gObject(sect); if (!o) return ;
	o.className= (o.className=='sectVis') ? 'sectHid' : 'sectVis';
	gObjectClsList[sect]=o.className;
}

/***********************************************
* misc cookie and command line functions 
***********************************************/


function cookieSet(sNm, sValue)
{
  if(sValue=="")document.cookie = sNm + "=" + escape(sValue) + "; path="+gHome+"; expires=Thu, 31 Dec 2099 ";
  else document.cookie = sNm + "=" + escape(sValue) + "; path="+gHome+"; ";
}

function cookieGet(sNm,deflt)
{
  var aCookie = document.cookie.split("; ");
  for (var i=0; i < aCookie.length; i++)
  {
      var aCrumb = aCookie[i].split("=");
      if(!aCrumb.length) return deflt;
      if (sNm == aCrumb[0]) 
          return unescape(aCrumb[1]);
  }
  //if(!deflt)deflt="";
  return deflt;
}

function protectFields(url)
{
    url=url.replace(/[+]/g,"%2B");//url=url.replace("+","%2B");
    url=url.replace(/[=]/g,"%3D");
    url=url.replace(/[%]/g,"%25");
    url=url.replace(/[&]/g,"%26");
    url=url.replace(/[?]/g,"%3F");
    //url=escape(url);
    //url=url.replace(/\"/g,"%22");
    return url;
}

function unprotectFields(url)
{
    url=unescape(url);
    url=url.replace(/[+]/g," ");
    return url;
}




/***********************************************
* Dynamic Ajax Content- Dynamic Drive DHTML code library (www.dynamicdrive.com)
* This notice MUST stay intact for legal use
* Visit Dynamic Drive at http://www.dynamicdrive.com/ for full source code
***********************************************/

var bustcachevar=1 //bust potential caching of external pages after initial request? (1=yes, 0=no)
var bustcacheparameter=""

function ajaxDynaRequestPage(url, containerid, callbackfun , ispost){
    
    var page_request = false
    if (window.XMLHttpRequest) // if Mozilla, Safari etc
        page_request = new XMLHttpRequest()
    else if (window.ActiveXObject){ // if IE
        try {
            page_request = new ActiveXObject("Msxml2.XMLHTTP")
        } 
        catch (e){
            try{
                page_request = new ActiveXObject("Microsoft.XMLHTTP")
            }
        catch (e){}
        }
    }
    else
        return false;

    
    page_request.onreadystatechange=function(){
        ajaxDynaLoadPage(page_request, containerid, callbackfun)
    }
    
    var posQuestion=url.indexOf("?");
    if (bustcachevar) //if bust caching of external page
        bustcacheparameter=(posQuestion!=-1)? "&"+new Date().getTime() : "?"+new Date().getTime()

    if(ispost){
        var paramset=""
        if( posQuestion!=-1 )paramset=url.substring(posQuestion+1);
        paramset+=bustcacheparameter;
        

        page_request.open('POST', url, true)
        page_request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        //page_request.setRequestHeader("Content-length", paramset.length);
        
        page_request.send(paramset);
    }else {
        page_request.open('GET', url+bustcacheparameter, true)
        page_request.send(null);
    }
}

function ajaxAutoUpdateLayer(container, text)
{
	var v=gObject(container);if(!v)return;
	if(container.indexOf("pre")==0)v.innerHTML="<pre>"+text+"</pre>";
	else v.innerHTML=text;
}


function ajaxDynaLoadPage(page_request, containerid, callbackfun)
{
	if (page_request.readyState == 4 && (page_request.status==200 || window.location.href.indexOf("http")==-1)) { 
        if(callbackfun!="")callbackfun (containerid,page_request.responseText);
        else ajaxAutoUpdateLayer(containerid,page_request.responseText); //document.getElementById(containerid).innerHTML=page_request.responseText;
     }
}


function ajaxDynaRequestAction(url,ispost){
    var page_request = false
    if (window.XMLHttpRequest) // if Mozilla, Safari etc
        page_request = new XMLHttpRequest()
    else if (window.ActiveXObject){ // if IE
        try {
            page_request = new ActiveXObject("Msxml2.XMLHTTP")
        } 
        catch (e){
            try{
                page_request = new ActiveXObject("Microsoft.XMLHTTP")
            }
        catch (e){}
        }
    }
    else
        return false;
    
    var posQuestion=url.indexOf("?");
    if (bustcachevar) //if bust caching of external page
        bustcacheparameter=(url.indexOf("?")!=-1)? "&"+new Date().getTime() : "?"+new Date().getTime()
    if(ispost){
        var paramset=""
        if( posQuestion!=-1 ){
            paramset=url.substring(posQuestion+1);
            url=url.substring(0,posQuestion);
        }
        paramset+=bustcacheparameter;
        
        alert("posting "+ url + "----------"+paramset);
        page_request.open('POST', url, true)
        page_request.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        //page_request.setRequestHeader("Content-length", paramset.length);
        page_request.send(paramset+bustcacheparameter);
    
    }else { 
        page_request.open('GET', url+bustcacheparameter, true)
        page_request.send(null);
    }
}


/***********************************************
* misc doc composition functions 
***********************************************/
        
function docMakeSelect(txt, curval, namebase, onchangefun )
{
    var arrt=txt.split("|");
    
    var selt="<select class='inputEditable' name='"+namebase+"' onchange='"+onchangefun+"' >";
    for ( var im=1; im<arrt.length; ++im) {
       selt+="<option value='"+arrt[im]+"' "+((curval==arrt[im]) ? "selected" : "") +">"+arrt[im]+"</option>";
    }
    selt+="</select>";                    
    return selt;
}

function docLocValue(fld, defval)
{
    var loc=""+document.location;
    var isrch=loc.indexOf(fld+"="); 
    if(isrch!=-1){
        var pc=loc.substring(isrch+fld.length+1);
        var esrch=pc.indexOf("&");
        if(esrch!=-1)pc=pc.substring(0,esrch);
        return unescape(pc);
    }
    return defval ? defval : "";
}

function docZoomShift( zoomX,  what, zmin )
{
	
	var op=what.substring(0,1);
	var coef=parseFloat(what.substring(1));
		
	if(op=='0'){
		zoomX[0]=0;
		zoomX[1]=1;
		return zoomX;//""+zoomstart+","+zoomsend;
	}
	
	zoomwin=zoomX[1]-zoomX[0];
	zoomctr=(zoomX[1]+zoomX[0])/2;
	if(!zmin)zmin=0.001;

	
	if(op=='*') zoomwin*=coef;
	else if(op=='/') zoomwin/=coef;
	else if(op=='+') zoomctr+=zoomwin*coef;
	else if(op=='-') zoomctr-=zoomwin*coef;
	else if(op=='=') zoomctr=coef;
	if(zoomwin>1)zoomwin=1;
	if(zoomwin<zmin)zoomwin=zmin;
	zoomX[0]=zoomctr-zoomwin/2;
	zoomX[1]=zoomctr+zoomwin/2;

	if(zoomX[0]<0){
		zoomX[0]=0;
		zoomX[1]=zoomX[0]+zoomwin;
	}
	if(zoomX[1]>1){
		zoomX[1]=1;
		zoomX[0]=zoomX[1]-zoomwin;
	}
	
	return zoomX; 
}       

var gDoc_assocArray=new Array();
function docAssocArray( keylist, vallist, spliter,  doempty) 
{
	if(doempty)
		gDoc_assocArray= new Array();
	
	var j,ia,iv;
	var jrr;
	if(!spliter )jrr=keylist.split(/\s,/);
	else jrr=keylist.split(spliter);
	
    if(!spliter )vrr=vallist.split(/\s,/);
	else vrr=vallist.split(spliter);
	
    for( j=0; j< jrr.length; ++j ){
		if(!jrr[j] || jrr[j].length==0) continue;
		    	
		// look for this element jrr[ij] in our array 
		for( ia=0; ia<gDoc_assocArray.length; ++ia ){
			if( gDoc_assocArray[ia][0]==jrr[j]) // found it  
				break;  
		}
		
		if( ia==gDoc_assocArray.length) { // didn't find this key : add it  
			gDoc_assocArray.push(new Array());
			gDoc_assocArray[ia][0]=jrr[j];
		}
		
        for ( il =0 ; il < vrr.length; ++il ) { 
            var val = vrr[il];
            if(!val || !val.length )continue;
            
		    for( iv=1 ; iv<gDoc_assocArray[ia].length; ++iv) { 
			    if( gDoc_assocArray[ia][iv]==val ) // if this value is already associated with this key  
				    break;
            }
            if(iv==gDoc_assocArray[ia].length)
        	    gDoc_assocArray[ia].push(val);
        }
	}
    
}

function printAssocArray( assArr) 
{
	var t="";
	for ( var i=0; i<assArr.length ; ++ i ){
		t+="#"+i+" "+assArr[i][0]+"["+assArr[i].length+"] = ";
		for (var j=1; j<assArr[i].length; ++j ) {
			t+="#"+j+ " "+assArr[i][j]+"  ";
		}
		t+="\n";
	}
	return t;
}

function listAssocArray( assArr, doIncl, inum ) 
{
	var totArr=new Array();
	var t="";
	for ( var i=0; i<assArr.length ; ++ i ){
		if(doIncl>0 && i!=inum)continue;
		if(doIncl<0 && i==inum)continue;
		
		for (var j=1; j<assArr[i].length; ++j ) {
			
			var k;
			for( k=0 ; k<totArr.length; ++k )
				if( totArr[k]==assArr[i][j] )break;
			if(k<totArr.length) continue;
			if(t.length)t+=",";
			t+=assArr[i][j];
			totArr[totArr.length]=assArr[i][j];
		}
	}
	//alert(t);
	return t;
}

function gDoc_flags() {}
gDoc_flags.display = { extended : 0x00000001, ordinal : 0x00000002 , showall : 0x00000004 };

function docAssArr_makeTable(prefix, assArr, cbFunc, container, dispFlags, filterlist  )
{
	if(assArr.length==0)return ;

    var frr=new Array ();
    if ( filterlist) frr = filterlist.split(/\s/);
    
    // output the header
	var t="<table class='QP_svcTbl'><tr>";
		if( dispFlags&gDoc_flags.display.ordinal )
			t+="<th>&bull;</th>"
		t+="<th>";
            if( dispFlags&gDoc_flags.display.showall )
                t+="<a href='javascript:"+cbFunc+"(-1,0,\"all\")' >";
            t+=prefix;
            if( dispFlags&gDoc_flags.display.showall )
                t+="</a>";
        t+="</th>"
	t+="</tr>";
	
	for( i=0 ; i<assArr.length ; ++i) {
        
        if( frr.length )   { // see if we filter this one out 
            for ( il=0; il<frr.length; ++il) if( frr[il].length && frr[il]==assArr[i][0])break;
            if(il==frr.length)continue;
        }

    	var idnam=prefix+"_"+assArr[i][0];
		t+= "<tr>";
		if( dispFlags&gDoc_flags.display.ordinal )
			t+="<td><input type=checkbox name='"+prefix+"_chk_"+assArr[i][0]+"' >"+(i+1)+"</td>";
		
		t+="<td>";
			if( dispFlags&gDoc_flags.display.extended )
				t+=ovis(idnam+"_extended","sectHid")+"&nbsp;";
			t+="<a href='javascript:"+cbFunc+"("+i+","+0+",\""+idnam+"\")' >"+assArr[i][0]+"</a>";
			if( dispFlags&gDoc_flags.display.extended ){
				t+="<span id='"+idnam+"_extended' class='sectHid' ><table border=0>";
				for( var ia=1;ia<assArr[i].length;  ++ia) 
					t+="<tr><td width=16></td><td><a href='javascript:"+cbFunc+"("+i+","+ia+",\""+prefix+assArr[i][ia]+"\")' >"+assArr[i][ia]+"</a></td></tr>";
				t+="</table></span>";
			}
		t+="</td>";
		t+="</tr>";
	}  
	t+="</table>";
	
	if(container)gObject(container).innerHTML=t;
	else return t;
}


function docAssArr_tabSetMakeChoice( prefix, isel , cnt, tohide, toshow )
{
	var hid=tohide.split(",");
	var sho=toshow.split(",");
	
	for( var i=0; i<hid.length; ++i ){var o=gObject(hid[i]);if(!o)continue;
		o.className="sectHid"; 
	}
	for( var i=0; i<sho.length; ++i ){var o=gObject(sho[i]);if(!o)continue;
		o.className="sectVis"; 
	}
	for ( var i=0; i<cnt; ++i ) { var o=gObject(prefix+i);if(!o)continue;
		if(i==isel)o.className="tab_selected";
		else o.className="tab_unselected";
	}

}



function docAssArr_makeTabset(prefix, assArr, cbFunc, container, filterlist  )
{
	if(assArr.length==0)return ;
	if(!cbFunc ) cbFunc = "docAssArr_tabSetMakeChoice";
	
	var frr=new Array ();
    if ( filterlist) frr = filterlist.split(/\s/);

    var t="<table cellspacing=0 cellpadding=0><tr>"; 
    
    for( i=0 ; i<assArr.length ; ++i) {
    	var tohide= listAssocArray( assArr, -1, i);
    	var toshow= listAssocArray( assArr, +1, i);
    	
        if( frr.length )   { // we if we filter this one out 
            for ( il=0; il<frr.length; ++il) if( frr[il].length && frr[il]==assArr[i][0])break;
            if(il==frr.length)continue;
        }
    	
		t+="<td>";
		t+="<table border=0 cellspacing=0 cellpadding=0  class='tab_unselected' id='"+prefix+""+i+"' ><tr>";

		t+="<td width=2  ></td>";
		t+="<td ><a href='javascript:"+cbFunc+"(\""+prefix+"\","+i+","+assArr.length+",\""+tohide+"\",\""+toshow+"\")' >"+assArr[i][0]+"</a></td>";
		t+="<td width=2 >&nbsp;</td>";
		t+="</tr></table>";	
		
		t+="</td>";
		
	}  
	t+="</tr></table>";
	//alert(t+ "<>"+container);
	if(container)gObject(container).innerHTML=t;
	else return t;
}

/***********************************************
* misc easy access functions 
***********************************************/
var gInitList="";
var gDataFormName="sCgi_DataForm";
var gDataForm;

function linkSelf(aSect, newin)
{
	if(newin)window.open(gCGI+"?cmd="+aSect,newin);
    else window.location.href=gCGI+"?cmd="+aSect;
}

function linkCmd(cmd, container, callback)
{
	
	if(callback=="-")ajaxDynaRequestPage(gCGI+"?cmd="+cmd,container,"");
    else if(callback)ajaxDynaRequestPage(gCGI+"?cmd="+cmd,container,callback);
    else ajaxDynaRequestAction(gCGI+"?cmd="+cmd);
}

function linkCGI(url, container, callback)
{
	if(callback=="-")ajaxDynaRequestPage(gCGI+"?"+url,container,"");
    else if(callback)ajaxDynaRequestPage(gCGI+"?"+url,container,callback);
    else ajaxDynaRequestAction(gCGI+"?"+url);
}

function setLocationTitle(txt)
{
	var v=gObject("cgiLocation");
	if(v)v.innerHTML=txt;
}
        
function gInit()
{
    document.onmousemove = gOnMouseMove;
	//if (window.addEventListener) window.addEventListener('DOMMouseScroll', gOnMouseWheel, false); /** DOMMouseScroll is for mozilla. */
	//window.onmousewheel = document.onmousewheel = gOnMouseWheel; /** IE/Opera. */
    
    gGetPgParams();
	gDataForm=document.forms[gDataFormName];
    
    if(gInitList.length) {
        eval(gInitList);
    }
}
 

function  formData(elem)
{
    var elem=gDataForm.elements[elem];if(!elem)return "";
    return elem.value;
}

/***********************************************
* misc ActionScript Related functions
***********************************************/
   

function asFindSWF(movieName) {
	if (navigator.appName.indexOf("Microsoft")!= -1) {
		return window[movieName];
	} else {
		return document[movieName];
	}
}






/**********************************************
* color functions 
**********************************************/


function randColor()
{
    return '#'+Math.floor(Math.random()*16777215).toString(16);
} 

var gClrTable = new Array (
    "#000000",
    "#7f7f7f",
    "#40B000",
	"#0000FF",
    "#A52A2A",
    "#D2691E",
    "#00008B",
    "#008B8B",
    "#B8860B",
    "#A9A9A9",
    "#006400",
    "#BDB76B",
    "#8B008B",
    "#556B2F",
    "#FF8C00",
    "#9932CC",
    "#8B0000",
    "#E9967A",
    "#8FBC8F",
    "#483D8B",
    "#2F4F4F",
    "#00CED1",
    "#9400D3",
    "#808080",
    "#0000CD",
    "#BA55D3",
    "#9370DB",
    "#3CB371",
    "#7B68EE",
    "#00FA9A",
    "#48D1CC",
    "#C71585",
    "#191970",
    "#000080",
    "#FFA500",
    "#FF4500",
    "#FF0000",
    "#4169E1",
    "#FF6347",
    "#40E0D0",
    "#EE82EE",
    "#F5DEB3",
    "#FFFF00",
	"#9ACD32",
    "#F0F8FF",
    "#FAEBD7",
    "#00FFFF",
    "#7FFFD4",
    "#F0FFFF",
    "#F5F5DC",
    "#FFE4C4",
    "#000000",
    "#FFEBCD",
    "#0000FF",
    "#8A2BE2",
    "#A52A2A",
    "#DEB887",
    "#5F9EA0",
    "#7FFF00",
    "#D2691E",
    "#FF7F50",
    "#6495ED",
    "#FFF8DC",
    "#DC143C",
    "#00FFFF",
    "#00008B",
    "#008B8B",
    "#B8860B",
    "#A9A9A9",
    "#006400",
    "#BDB76B",
    "#8B008B",
    "#556B2F",
    "#FF8C00",
    "#9932CC",
    "#8B0000",
    "#E9967A",
    "#8FBC8F",
    "#483D8B",
    "#2F4F4F",
    "#00CED1",
    "#9400D3",
    "#FF1493",
    "#00BFFF",
    "#696969",
    "#1E90FF",
    "#B22222",
    "#FFFAF0",
    "#228B22",
    "#FF00FF",
    "#DCDCDC",
    "#F8F8FF",
    "#FFD700",
    "#DAA520",
    "#808080",
    "#008000",
    "#ADFF2F",
    "#F0FFF0",
    "#FF69B4",
    "#CD5C5C",
    "#4B0082",
    "#FFFFF0",
    "#F0E68C",
    "#E6E6FA",
    "#FFF0F5",
    "#7CFC00",
    "#FFFACD",
    "#ADD8E6",
    "#F08080",
    "#E0FFFF",
    "#FAFAD2",
    "#90EE90",
    "#D3D3D3",
    "#FFB6C1",
    "#FFA07A",
    "#20B2AA",
    "#87CEFA",
    "#778899",
    "#B0C4DE",
    "#FFFFE0",
    "#00FF00",
    "#32CD32",
    "#FAF0E6",
    "#FF00FF",
    "#800000",
    "#66CDAA",
    "#0000CD",
    "#BA55D3",
    "#9370DB",
    "#3CB371",
    "#7B68EE",
    "#00FA9A",
    "#48D1CC",
    "#C71585",
    "#191970",
    "#F5FFFA",
    "#FFE4E1",
    "#FFE4B5",
    "#FFDEAD",
    "#000080",
    "#FDF5E6",
    "#808000",
    "#6B8E23",
    "#FFA500",
    "#FF4500",
    "#DA70D6",
    "#EEE8AA",
    "#98FB98",
    "#AFEEEE",
    "#DB7093",
    "#FFEFD5",
    "#FFDAB9",
    "#CD853F",
    "#FFC0CB",
    "#DDA0DD",
    "#B0E0E6",
    "#800080",
    "#FF0000",
    "#BC8F8F",
    "#4169E1",
    "#8B4513",
    "#FA8072",
    "#F4A460",
    "#2E8B57",
    "#FFF5EE",
    "#A0522D",
    "#C0C0C0",
    "#87CEEB",
    "#6A5ACD",
    "#708090",
    "#FFFAFA",
    "#00FF7F",
    "#4682B4",
    "#D2B48C",
    "#008080",
    "#D8BFD8",
    "#FF6347",
    "#40E0D0",
    "#EE82EE",
    "#F5DEB3",
    "#FFFFFF",
    "#F5F5F5",
    "#FFFF00",
    "#9ACD32"
    );

    




