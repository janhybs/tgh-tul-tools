$( document ).ready(
    function () {
        var selectedProblem  = $ (document.forms['send-code']['selected-problem']);
        var problemName      = $ ('.problem-name');
        var problemURL       = $ ('.problem-url');
        var langs            = {c: ""}

        selectedProblem.change (function (e) {
            var value = selectedProblem.val ();
            var item;

            for (var i = 0; i < problemName.size (); i++) {
                item = $(problemName[i]);
                item.html ((item.data('prefix') ? item.data('prefix') : '') + value)
            }

            for (var i = 0; i < problemURL.size (); i++) {
                item = $(problemURL[i]);
                item.attr ('href', (item.data('prefix') ? item.data('prefix') : '') + value)
            }
        });

        selectedProblem.trigger ('change');

        function escapeHtml(text) {
          return text
              .replace(/&/g, "&amp;")
              .replace(/</g, "&lt;")
              .replace(/>/g, "&gt;")
              .replace(/"/g, "&quot;")
              .replace(/'/g, "&#039;");
        }


        var showLanguage = function (name) {
            var source = $('#source-code-example');
            var lang   = $ (document.forms['send-code']['selected-language']).val ();
            var langs = $.sourceCodeExamples['langs'];

            source.removeClass ();
            source.addClass (lang);
            source.html (escapeHtml(langs[lang]));
            hljs.initHighlighting ();
            selectedLanguageHolder.show ();
            selectedLanguageHolder.css ("display", "block");
        }



        var selectedLanguage        = $ (document.forms['send-code']['selected-language']);
        var selectedLanguageHolder  = $ ('#source-code-example-holder');
        var langName                = $ ('.lang-name');
        var langURL                 = $ ('.lang-url');
        var item;
        $.sourceCodeExamples = undefined;


        for (var i = 0; i < langURL.size (); i++) {
            item = $ (langURL[i]);
            langURL.click (function () {

                if (selectedLanguageHolder.is (":visible")) {
                    selectedLanguageHolder.hide ();
                } else {
                    if ($.sourceCodeExamples === undefined) {
                        $.sourceCodeExamples = false;
                        
                        $.getJSON ('./problems/source-code-examples.json', function( data ) {
                            $.sourceCodeExamples = data;
                            showLanguage ();
                        });
                    } else if ($.sourceCodeExamples !== false) {
                        showLanguage ();
                    }
                }
            });
        }

        selectedLanguage.change (function (e) {
            var value = selectedLanguage.val ();
            var item;

            for (var i = 0; i < langName.size (); i++) {
                item = $(langName[i]);
                item.html ((item.data('prefix') ? item.data('prefix') : '') + value)
            }

            if (selectedLanguageHolder.is(":visible") && $.sourceCodeExamples)
                showLanguage ();
        });

        selectedLanguage.trigger ('change');
        hljs.initHighlighting ();




    }
);