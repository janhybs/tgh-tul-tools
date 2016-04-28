$( document ).ready(
    function () {
        var processing = $('#processing');
        var output = $('#output');
        var exitCode = $('#exit-code').html();
        var outputHolder = $('#output-holder');
        var outputHeader = $('#output-header');

        var msgs = {
            '0': 'Řešení je správné!',
            '1': 'Neznámá chyba',
            '2': 'Chyba při kompilaci',
            '3': 'Chyba při behu programu',
            '4': 'Chybný výstup',
        }
        var msg = msgs.hasOwnProperty (exitCode) ? msgs[exitCode] : msgs['1'];

        var opts = 'fast'//;{duration: 400, easing: 'fade'};
        var cls = 'alert-success';


        
        if (exitCode != "0") {
            cls = 'alert-danger';
        }

        outputHolder.removeClass ('alert-success');
        outputHolder.addClass (cls);
        outputHeader.html (msg);

        processing.hide (opts);
        outputHolder.show (opts);

    }
);
