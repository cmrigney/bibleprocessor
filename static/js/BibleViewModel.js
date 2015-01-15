var BibleViewModel = function() {
    var self = this;
    self.openBook = ko.observable('Genesis');
    self.openChapter = ko.observable(1);
    self.openMaxChapter = ko.observable();
    self.bibleDisplay = ko.observableArray();
    self.crossRefDisplay = ko.observableArray();
    self.crossRefSource = ko.observable();
    self.canLoadMoreRefs = ko.observable(false);

    self.clickedOnWord = ko.observable();
    self.clickedOnWordFreq = ko.observable();

    self.loadAllRefs = function() {
        var val = self.crossRefSource();
        self.canLoadMoreRefs(false);
        $.getJSON('/crossrefs/?limit=9999999&book=' + self.openBook() + '&chapter=' + val["Chapter"] + '&verse=' + val["Verse"], function(lst) {
            self.crossRefDisplay(lst);
        });
    };

    self.reloadOpenBible = function() {
        $("#openBibleBody").hide();
        $("#openBiblePanel").scrollTop(0);
        $.getJSON('/getbook/?book=' + self.openBook() + '&chapter=' + self.openChapter(), function(data) {
            self.bibleDisplay(data.values);
            self.openMaxChapter(data.meta.MaxChapter);
            $('.verseNum:first').html('&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' + $('.verseNum:first').html());
            $(".verse").lettering('words');
            $(".verse").children().addClass("wordHighlighted");
            $(".verse").children().click(function() {
                var raw = $(this).text();
                var word = raw.replace(/\W/g, '');
                self.clickedOnWord(word);
                $.getJSON('/wc/?word=' + word.toLowerCase(), function(data) {
                    self.clickedOnWordFreq(data.count);
                });
            });

            $(".verse").unbind("click");
            $(".verse").click(function() {
                var idx = $(".verse").index(this);
                var val = self.bibleDisplay()[idx];
                if(val == self.crossRefSource())
                    return;
                $("#crossRefContent").hide();
                $(".verse").removeClass("highlighted");
                $(this).addClass("highlighted");
                self.canLoadMoreRefs(false);
                self.crossRefSource(val);
                $.getJSON('/crossrefs/?limit=6&book=' + self.openBook() + '&chapter=' + val["Chapter"] + '&verse=' + val["Verse"], function(lst) {
                    if(lst.length >= 6) {
                        self.canLoadMoreRefs(true);
                        lst.pop();
                    }
                    self.crossRefDisplay(lst);
                    $("#crossRefContent").fadeIn();
                });

            });

            $("#openBibleBody").fadeIn();
        });
    }

    self.showVisualizeWord = function() {
        $("#visWordModal").modal('show');
    };

    self.prevChapter = function() {
        self.openChapter(self.openChapter()-1);
        self.reloadOpenBible();
    }

    self.nextChapter = function() {
        self.openChapter(self.openChapter()+1);
        self.reloadOpenBible();
    }

    self.searchTerm = ko.observable('');
	self.relatedVerses = ko.observableArray();
	self.canLoadMoreSearchVerses = ko.observable(false);
	self.loadingSearchedVerses = ko.observable(false);
	self.searchTerms = ko.computed(function() {
			return replaceAll(" ",":",self.searchTerm().toLowerCase());
		});

	self.loadAllSearchVerses = function() {
	    self.canLoadMoreSearchVerses(false);
	    var order = $("#selectType").val();
	    self.loadingSearchedVerses(true);
		$.getJSON('/w/?limit=99999999&ordered=' + order + '&words=' + self.searchTerms(), function (data) {
		    self.loadingSearchedVerses(false);
			self.relatedVerses(data);
		});
	};

	self.getRelatedVerses = function(){
		var order = $("#selectType").val();
		self.canLoadMoreSearchVerses(false);
		self.loadingSearchedVerses(true);
		$.getJSON('/w/?limit=11&ordered=' + order + '&words=' + self.searchTerms(), function (data) {
		    $("#verseLocation").hide();
		    if(data.length > 10) {
		        self.canLoadMoreSearchVerses(true);
		    }
		    self.loadingSearchedVerses(false);
			self.relatedVerses(data.slice(0, 5));
			window.location.hash = '';
			window.location.hash = '#verseLocation';
			$("#verseLocation").fadeIn(2500);
		});
	};


    self.reloadOpenBible();
}


$(function () {
    viewModel = new BibleViewModel();
    ko.applyBindings(viewModel);

    $("#visWordModal").on('shown.bs.modal', function() {
            $("#visWordBody").html('<iframe style="width: 100%; height: 100%" src="viswordwidget.html?word=' + viewModel.clickedOnWord() + '"></iframe>');
    });
    $("#visWordModal").on('hidden.bs.modal', function() {
            $("#visWordBody").html('');
    });



    var opts = {
      lines: 13, // The number of lines to draw
      length: 15, // The length of each line
      width: 5, // The line thickness
      radius: 15, // The radius of the inner circle
      corners: 0.4, // Corner roundness (0..1)
      rotate: 55, // The rotation offset
      direction: 1, // 1: clockwise, -1: counterclockwise
      color: '#000', // #rgb or #rrggbb or array of colors
      speed: 1.4, // Rounds per second
      trail: 16, // Afterglow percentage
      shadow: false, // Whether to render a shadow
      hwaccel: false, // Whether to use hardware acceleration
      className: 'spinner', // The CSS class to assign to the spinner
      zIndex: 2e9, // The z-index (defaults to 2000000000)
      top: '50%', // Top position relative to parent
      left: '50%' // Left position relative to parent
    };

    var target = document.getElementById('networkLoader');
	var spinner = new Spinner(opts).spin(target);
});


function replaceAll(find, replace, str) {
  return str.replace(new RegExp(find, 'g'), replace);
}

function getUrlParameter(sParam)
{
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++)
    {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == sParam)
        {
            return sParameterName[1];
        }
    }
}