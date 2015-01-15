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
	
var ScriptureLookupViewModel = function () {
    var self = this;


	self.resetNetworkWithWord = function() {
		var txt = self.wordOfNetwork();
		if(txt != null && txt != '') {
			resetGraph(txt.toLowerCase());
		}
	};

	self.loadingNetworkVerses = ko.observable(false);
	self.networkVerses = ko.observableArray();
	self.canLoadMoreNetworkVerses = ko.observable(false);
	self.interactionString = ko.observable("");

	self.loadMoreVerses = function() {
		self.canLoadMoreNetworkVerses(false);
		self.loadingNetworkVerses(true);
		var words = self.interactionString().split(' ').join(':'); //get in proper format
		$.getJSON('/w/?ordered=1&limit=9999999&words=' + words, function (data) {
			self.loadingNetworkVerses(false);
			self.networkVerses(data);
		});
	};

	self.wordOfNetwork = ko.observable('');

	self.statsOfWord = ko.observable('');
	self.statsView = ko.observable();
	self.getWordStats = function () {
		var word = self.statsOfWord();
		$.getJSON('/wc/?word=' + word, function (data) {
		    $("#statsData").hide();
			self.statsView(data);
			window.location.hash = '';
			window.location.hash = '#statsData';
			$("#statsData").fadeIn(2500);
		});
	}
}

var viewModel = null;

$(function () {
    $("#verseLocation").hide();

    viewModel = new ScriptureLookupViewModel();
	ko.applyBindings(viewModel);


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

	var wordToShow = getUrlParameter('word');
	if(typeof wordToShow !== "undefined") {
		viewModel.wordOfNetwork(wordToShow);
		viewModel.resetNetworkWithWord();
	}
});