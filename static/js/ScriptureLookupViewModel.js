function replaceAll(find, replace, str) {
  return str.replace(new RegExp(find, 'g'), replace);
}
	
var ScriptureLookupViewModel = function () {
    var self = this;
	self.searchTerm = ko.observable('');
	self.relatedVerses = ko.observableArray();
	self.searchTerms = ko.computed(function() {
			return replaceAll(" ",":",self.searchTerm().toLowerCase());
		});
	
	self.getRelatedVerses = function(){
		console.log(self.searchTerms());
		var order = $("#selectType").val();
		$.getJSON('/w/?ordered=' + order + '&words=' + self.searchTerms(), function (data) {
		    $("#verseLocation").hide();
			self.relatedVerses(data);
			window.location.hash = '';
			window.location.hash = '#verseLocation';
			$("#verseLocation").fadeIn(2500);
		});
	};

	self.resetNetworkWithWord = function() {
		var txt = self.wordOfNetwork();
		if(txt != null && txt != '') {
			resetGraph(txt.toLowerCase());
		}
	};

	self.loadingNetworkVerses = ko.observable(false);
	self.networkVerses = ko.observableArray();
	self.interactionString = ko.observable("");

	self.wordOfNetwork = ko.observable('');
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
})