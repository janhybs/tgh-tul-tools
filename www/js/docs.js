$( document ).ready(
    function () {
        var regexp = /.*problems\/(\w+)/gm;
        var submitSolution = $('#submit-solution');
        var problem = regexp.exec (document.URL)[1];
        var btn = $('<a href="/?p='+problem+'" class="btn btn-success"><span class="glyphicon glyphicon-send" aria-hidden="true"></span> Submit solution</a>');
        submitSolution.append (btn);
    }
);