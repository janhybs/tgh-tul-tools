$( document ).ready(
    function () {
        var processing = $('#processing');
        var output = $('#output');
        var exitCode = $('#exit-code').html();
        var outputHolder = $('#output-holder');
        var outputHeader = $('#output-header');
        var resultSummary = $('#result-summary');

        var msgs = {
            '0': 'Běh proběhl bez problémů',
            '1': 'Řešení je správné!',
            '3': 'Chybný výstup',
            '10': 'Chyba při kompilaci',
            '20': 'Chyba při behu programu',
            '100': 'Neznámá chyba',
        }
        var msg = msgs.hasOwnProperty (exitCode) ? msgs[exitCode] : msgs['100'];

        var opts = 'fast'//;{duration: 400, easing: 'fade'};
        var cls = 'alert-success';


        
        if (Number(exitCode) > 1) {
            cls = 'alert-danger';
        }

        outputHolder.removeClass ('alert-success');
        // outputHolder.addClass (cls);
        outputHeader.html (msg);

        processing.hide (opts);
        outputHolder.show (opts);
        
        var resultSummary = $('#result-summary');
        var rules = [
          [/(\[OK\])/gmi, '<span class="result-ok">$1</span>'],
          [/(\[ER\])/gmi, '<span class="result-error">$1</span>'],
          [/(Odevzdane reseni je SPRAVNE)/gmi, '<span class="result-ok">$1</span>'],
          [/(Odevzdane reseni je CHYBNE)/gmi, '<span class="result-error">$1</span>'],
        ];
        
        var summary = resultSummary.html();
        for (var rule in rules) {
          summary = summary.replace(rules[rule][0], rules[rule][1]);
        }
        resultSummary.html(summary);

    }
);
