var pbar = document.getElementById('pbar');
var duration = 5 + 30 * Number(document.getElementById('lang-scale').innerHTML);
var current = Date.now();
var future = Date.now() + duration*1000;
var tid = setInterval(function() {
    // # update pbar width
    var current = Date.now();
    prc = ((duration * 1000 - (future - current)) / duration) / 10;
    pbar.style.width = prc+"%";
    
    // # stop pbar
    if ((future - current) <= 0) clearInterval(tid);
}, 500);
