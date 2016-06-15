var pbar = document.getElementById('pbar');
var total = 75;
var current = 0;
var tid = setInterval(function() {
    // # update pbar width
    current++;
    pbar.style.width = ((100/total) * current)+"%";
    
    // # stop pbar
    if (current == total) clearInterval(tid);
}, 1000);