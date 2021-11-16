var current="Losowanie już się odbyło"
var montharray=new Array("Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec")
var zostalo = document.getElementById("zostalo");

function countdown(yr,m,d){
theyear=yr;themonth=m;theday=d
var today=new Date()
var todayy=today.getYear()
if (todayy < 1000) todayy+=1900
var todaym=today.getMonth()
var todayd=today.getDate()
var todayh=today.getHours()
var todaymin=today.getMinutes()
var todaysec=today.getSeconds()
var todaystring=montharray[todaym]+" "+todayd+", "+todayy+" "+todayh+":"+todaymin+":"+todaysec
futurestring=montharray[m-1]+" "+d+", "+yr
dd=Date.parse(futurestring)-Date.parse(todaystring)
dday=Math.floor(dd/(60*60*1000*24)*1)
dhour=Math.floor((dd%(60*60*1000*24))/(60*60*1000)*1)
dmin=Math.floor(((dd%(60*60*1000*24))%(60*60*1000))/(60*1000)*1)
dsec=Math.floor((((dd%(60*60*1000*24))%(60*60*1000))%(60*1000))/1000*1)
        if(dday<=0&&dhour<=0&&dmin<=0){
        zostalo.innerHTML=current
        return
        }else if(dday<=0&&dhour<=0){
        zostalo.innerHTML=dmin+" minut, i "+dsec+" sekund"
        setTimeout("countdown(theyear,themonth,theday)",1000)
        }else if(dday<=0){
        zostalo.innerHTML=dhour+" godzin, "+dmin+" minut, i "+dsec+" sekund"
        setTimeout("countdown(theyear,themonth,theday)",1000)
        }else{
        zostalo.innerHTML=dday+ " Dni, "+dhour+" godzin, "+dmin+" minut, i "+dsec+" sekund"
        setTimeout("countdown(theyear,themonth,theday)",1000)
        }
}
//Odpalamy date z parametrami rok/miesiąc/dzień
//countdown(2020,11,30)

intval = window.setInterval(move_reni, 30);

var reni_x=-500;
var reni=document.getElementById('reniferek').style;
function move_reni(){
  reni.backgroundPositionX=reni_x;
  reni_x=reni_x+1;
  if(reni_x>document.body.clientWidth+500)
  {
    reni_x=-500;
    reni.backgroundPositionY=Math.random()*document.body.clientHeight;
  }

}

