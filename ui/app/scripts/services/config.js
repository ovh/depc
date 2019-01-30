'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.config
 * @description
 * # config
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('config', function () {
    var getDepcEndpoint = function() {
      var apiEndpoint = 'http://localhost:5000/v1';
      return apiEndpoint
    };

    var getThresholds = function(level) {
      var thresholds = {
        'warning': 98,
        'error': 95
      };

      return thresholds[level];
    };

    var getPanelByLevel = function(level) {
      var panels = {
        'unknown': {
          'key': 'unknown',
          'class': 'panel-unknown',
          'text': 'There is no data'
        },
        'pending': {
          'key': 'pending',
          'class': 'panel-unknown',
          'text': 'There is no data'
        },
        'ok': {
          'key': 'ok',
          'class': 'panel-success',
          'text': 'All monitored dependencies seem to be fine.'
        },
        'warning': {
          'key': 'warning',
          'class': 'panel-warning',
          'text': 'Some monitored dependencies seem to be in a <strong>warning</strong> state.'
        },
        'critical': {
          'key': 'critical',
          'class': 'panel-critical',
          'text': 'Some monitored dependencies seem to be in a <strong>critical</strong> state.'
        }
      }

      return panels[level];
    };

    var getGraphSchema = function(nodes, edges, colorGraph) {
      var data = {
        nodes: nodes,
        edges: edges
      };

      // Set a custom color based on the label.
      // We keep a cache of the colors to not
      // use ColorHash for an already seen label.
      var colors = {};
      var colorHash = new ColorHash();
      for (var i in nodes) {
        var title = nodes[i]['title'];
        if (Object.keys(colors).indexOf(title) > -1) {
          nodes[i]['color'] = colors[title];
        } else {
          var color;
          if (colorGraph == null || colorGraph[nodes[i].title] == null) {
            color = colorHash.hex(title);
          } else {
              color= colorGraph[nodes[i].title];
          }
          colors[title] = color;
          nodes[i]['color'] = color;
        }
      }

      var options = {
        height: '300px',
        layout: {
            randomSeed: 2
        },
        nodes: {
            shape: 'dot',
            size: 24,
            font: {
                size: 16
            },
            borderWidth: 2,
            shadow:true
        },
        edges: {
            width: 1
        },
        physics: {
          barnesHut: {
            centralGravity: 0.10
          },
          minVelocity: 0.75
        },
        interaction: {
          hideEdgesOnDrag: false
        }
      };

      var events = {
        'dragging': function (params) {
          var nodes_container = this.body.data.nodes;
          var nodes_selection = nodes_container.get(params.nodes);
          nodes_selection.forEach(function(node) {
            node.physics = false;
          });
          nodes_container.update(nodes_selection);
        }
      };

      return {
        'data': data,
        'options': options,
        'events': events
      }
    };


    var getStateByQos = function(qos) {
      var type = 'unknown';
      var value = parseFloat(qos);

      if ( value >= parseFloat(98) ) {
          type = 'ok';
      } else if ( value >= parseFloat(90)) {
          type = 'warning';
      } else {
          type = 'critical';
      }

      return type;
    };

    var getLabelClassByQos = function(qos) {
      var label = 'label-default';
      var value = parseFloat(qos);

      if ( value >= parseFloat(98) ) {
          label = 'label-success';
      } else if ( value >= parseFloat(90)) {
          label = 'label-warning';
      } else if ( value >= parseFloat(0)) {
          label = 'label-danger';
      }

      return label;
    };

    var monthsHistoryCount = function() {
      return 4;
    };

    function isEmpty(map) {
       for(var key in map) {
          return !map.hasOwnProperty(key);
       }
       return true;
    }

    var getConfigGraph = function(nodes, edges) {
      var data = {
        nodes: nodes,
        edges: edges
      };

      var options = {
        height: '500px',
        layout: {
          hierarchical: {
            direction: "UD",
            sortMethod: "directed",
            nodeSpacing: 150,
            levelSeparation: 200,
            edgeMinimization: true
          }
        },
        edges: {
          smooth: {
            roundness: 0.4,
            forceDirection: 'vertical'
          },
          arrows: {to : true }
        },
        physics:false
      };

      return {
        'data': data,
        'options': options,
        'events': {}
      }
    };

    var getSlideBg = function(qos) {
        var bg = null;
        if ( parseFloat(qos) < getThresholds('error') ) {
            bg = 'bg-error';
        } else if ( parseFloat(qos) < getThresholds('warning') ) {
            bg = 'bg-warning';
        } else {
            bg = 'bg-success';
        }
        return bg;
    };

    return {
      depc_endpoint: getDepcEndpoint,
      getThresholds: getThresholds,
      graph_schema: getGraphSchema,
      getStateByQos: getStateByQos,
      getPanelByLevel: getPanelByLevel,
      monthsHistoryCount: monthsHistoryCount,
      isEmpty: isEmpty,
      getLabelClassByQos: getLabelClassByQos,
      getConfigGraph: getConfigGraph,
      getSlideBg: getSlideBg
    }

  });
