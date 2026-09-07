let timerSeconds = 25*60;
let timerRunning = false;
let timerInterval = null;
let timerMode = "FOCUS";

function renderTimer(){
  const el=document.getElementById("timerDisplay");
  const mode=document.getElementById("timerMode");
  if(!el) return;
  const m=String(Math.floor(timerSeconds/60)).padStart(2,"0");
  const s=String(timerSeconds%60).padStart(2,"0");
  el.textContent=`${m}:${s}`;
  mode.textContent=timerMode;
}
function setTimer(minutes){
  pauseTimer();
  timerSeconds=minutes*60;
  timerMode=minutes<=5?"BREAK":"FOCUS";
  renderTimer();
}
function startTimer(){
  if(timerRunning) return;
  timerRunning=true;
  timerInterval=setInterval(()=>{
    if(timerSeconds<=0){
      pauseTimer();
      if(timerMode==="FOCUS"){
        fetch("/sessions",{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:"minutes=25"})
          .then(r=>r.json()).then(()=>{
            const s=document.getElementById("sessionStatus");
            if(s) s.textContent="Focus session saved! Great work.";
          });
        setTimer(5);
      }else setTimer(25);
      return;
    }
    timerSeconds--;
    renderTimer();
  },1000);
}
function pauseTimer(){
  timerRunning=false;
  if(timerInterval){clearInterval(timerInterval);timerInterval=null;}
}
function resetTimer(){pauseTimer();timerSeconds=25*60;timerMode="FOCUS";renderTimer();}
document.addEventListener("DOMContentLoaded",renderTimer);


// StudyOS PWA installation
let deferredInstallPrompt = null;
const installButton = document.getElementById("install-app");

window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredInstallPrompt = event;
  if (installButton) installButton.hidden = false;
});

if (installButton) {
  installButton.addEventListener("click", async () => {
    if (!deferredInstallPrompt) return;
    deferredInstallPrompt.prompt();
    await deferredInstallPrompt.userChoice;
    deferredInstallPrompt = null;
    installButton.hidden = true;
  });
}

window.addEventListener("appinstalled", () => {
  deferredInstallPrompt = null;
  if (installButton) installButton.hidden = true;
});
