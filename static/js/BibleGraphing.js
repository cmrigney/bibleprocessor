$(function() {
  drawNetwork();
});

var nodes = new vis.DataSet();
nodes.add([
    {id: 1, label: 'jesus'}
]);

var edges = new vis.DataSet();

var networkData = { nodes: nodes, edges: edges };

/*
var nodes = [
    {id: 1, label: 'jesus'}
];
*/
var runningNodeId = 2;

  // create an array with edges
  /*
var edges = [
];
*/

function resetGraph(word) {
    nodes.clear();
    nodes.add([ { id: 1, label: word } ]);
    edges.clear();
    runningNodeId = 2;
    drawNetwork();
}

function removeNodesAfter(nodeId) {
    var newNodes = [];
    var newEdges = [];

    for(var i = 0; i < nodes.length; i++) {
        if(nodes[i].id <= nodeId) {
            newNodes.push(nodes[i]);
            for(var x = 0; x < edges.length; x++) {
                if(edges[x].from == nodes[i].id) {
                    newEdges.push(edges[x]);
                }
            }
        }
    }

    edges = newEdges;
    nodes = newNodes;
}

/*
function nodeWithId(id) {
    return nodes.filter(function(val) {
        return val.id == id;
    })[0];
}
*/

function nodeWithId(id) {
    return nodes.get({ filter: function(val) {
        return val.id == id;
    }})[0];
}

function removeExcept(lst, lastNode) {
    if(lst.length <= 1) {
        return;
    }

    removeEdges = edges.getIds({ filter: function(val) {
        return lst.indexOf(val.from) < 0 && val.to != lastNode;
    }});

    edges.remove(removeEdges);

    removeNodes = nodes.getIds({ filter: function(val) {
        return edges.get({ filter: function(ed) { return ed.from == val.id || ed.to == val.id; }}).length == 0;
    }});

    nodes.remove(removeNodes);
}

function hasNodesFrom(nodeId) {
    return edges.get({ filter: function(val) {
        return val.from == nodeId;
    }}).length > 0;
}

function forEachNodeIn(lst, func) {
    for(var i = 0; i < nodes.get().length; i++) {
        if(lst.indexOf(nodes.get()[i].id) >= 0) {
            func(nodes.get()[i]);
        }
    }
}

function forEachNode(func) {
    for(var i = 0; i < nodes.get().length; i++) {
        func(nodes.get()[i]);
    }
}


function traceInternal(currentNode, targetId, runningList) {
  runningList.push(currentNode);
  if(currentNode == targetId) {
    return true;
  }

  for(var i = 0; i < edges.get().length; i++) {
    if(edges.get()[i].from == currentNode) {
        if(traceInternal(edges.get()[i].to, targetId, runningList)) {
            return true;
        }
    }
  }

  runningList.pop();
  return false;
}

function getTraceToNode(id) {
  lst = [];
  traceInternal(1, id, lst);
  return lst;
}

function formNamesFromList(lst) {
    var result = "";
    for(var id in lst) {
        result += nodeWithId(lst[id]).label + ":";
    }
    result = result.slice(0, result.length-1);
    return result;
}


function nodeSelected(properties) {
  if(properties.nodes.length == 0)
    return;

  var selectedNodeId = parseInt(properties.nodes[0]);

  var nodeList = getTraceToNode(selectedNodeId);
  var words = formNamesFromList(nodeList);
  //removeNodesAfter(selectedNodeId);
  removeExcept(nodeList, selectedNodeId);

  viewModel.loadingNetworkVerses(true);

  viewModel.interactionString(words.replace(/:/g, ' '));
  viewModel.canLoadMoreNetworkVerses(false);
  viewModel.networkVerses([]);
  $.getJSON('/w/?ordered=1&limit=6&words=' + words, function (data) {
            viewModel.loadingNetworkVerses(false);
            $("#networkVerseDiv").hide();
            if(data.length > 5) {
                viewModel.canLoadMoreNetworkVerses(true);
            }
			viewModel.networkVerses(data.slice(0, 5));
			window.location.hash = '';
			window.location.hash = "#versesBody";
			$("#networkVerseDiv").slideDown(1500);

		});

  $.getJSON('/freq/?words=' + words, function (data) {
			topData = data.slice(0, 5);
			if(!hasNodesFrom(selectedNodeId)) {
                for(var i = 0; i < topData.length; i++) {
                  nodes.add({id: runningNodeId, label: topData[i]._id});
                  edges.add({from: selectedNodeId, to: runningNodeId});
                  runningNodeId++;
                }
			}

			forEachNode(function(n) {
			    if(nodeList.indexOf(n.id) >= 0) {
			        nodes.update({ id: n.id, group: 1});
			        //n.group = 1;
			    }
			    else {
			        nodes.update({ id: n.id, group: -1});
			        //delete n.group;
			    }
			});

			//drawNetwork([selectedNodeId]);
		});
}

function drawNetwork() {
  drawNetwork(null);
}

function drawNetwork(selectedNodes) {
  // create a network
  var container = document.getElementById('mynetwork');
  /*
  var data = {
    nodes: nodes,
    edges: edges
  };
  */
  var options = {
    groups: {
        1: {
            color: {
              border: 'black',
              background: 'green',
              highlight: {
                border: 'yellow',
                background: 'orange'
              }
            }
        }
    }
   };
  var network = new vis.Network(container, networkData, options);
  network.on('select', nodeSelected);

  if(selectedNodes != null) {
    network.selectNodes(selectedNodes);
  }
}