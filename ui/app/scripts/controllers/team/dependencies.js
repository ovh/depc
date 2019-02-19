'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:DependenciesCtrl
 * @description
 * # DependenciesCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('DependenciesCtrl', function ($routeParams, $location, $filter, $confirm, toastr, config, modalService, teamsService, dependenciesService) {
    var self = this;
    self.teamName = $routeParams.team;

    self.selectedLabel = null;
    self.selectedNode = null;
    self.nodeProperties = {};
    self.loadNodes = false;
    self.includeOldNodes = false;
    self.selectedDay = moment().format('YYYY-MM-DD');

    self.resultTitle = null;
    self.nodeSearched = null;
    self.nodesResult = [];

    self.graph = null;
    self.legend = {};
    self.dependenciesLoading = false;
    self.dependencies = {};

      self.init = function () {
          self.labels = [];
          self.labelsLoading = true;

          if ($routeParams.day) {
            self.selectedDay = $routeParams.day;
          }

          if ($routeParams.old) {
            self.includeOldNodes = $routeParams.old;
          }

          teamsService.getTeamByName(self.teamName).then(function (response) {
              self.team = response.data;

              dependenciesService.getTeamLabels(self.team.id).then(function (response) {
                  self.labels = response.data;
                  self.labelsLoading = false;

                  if ($routeParams.label) {
                      self.selectLabel($routeParams.label);

                      if ($routeParams.node) {
                          self.selectNode($routeParams.node);
                      }
                  }
              });
          });
      };
      self.init();

      self.selectLabel = function (label) {
          $location.search('label', label);
          self.selectedLabel = label;
      };

      // Fetch some nodes as examples for the user
      self.loadExamples = function () {
          self.loadNodes = true;
          self.selectedNode = null;
          self.nodesResult = [];
          self.resultTitle = null;
          dependenciesService.getTeamLabelNodes(self.team.id, self.selectedLabel, null, 10, true).then(function (response) {
              self.nodesResult = response.data;
              self.resultTitle = 'random';
              self.loadNodes = false;
          });
      };

      // Search nodes by their name
      self.searchNode = function () {
        self.loadNodes = true;
          self.selectedNode = null;
          self.nodesResult = [];
          self.resultTitle = null;
          dependenciesService.getTeamLabelNodes(self.team.id, self.selectedLabel, self.nodeSearched).then(function (response) {
              self.nodesResult = response.data;
              self.resultTitle = self.nodesResult.length + ' nodes';
              self.loadNodes = false;
          });
      };

      self.resetNode = function () {
          self.selectedNode = null;
          self.nodesResult = [];
          self.resultTitle = null;
          self.graph = null;
          self.legend = {};
          self.dependencies = {};
          self.dependenciesStatus = {};

          // Reset the query parameters
          $location.search('node', null);
          $location.search('start', null);
          $location.search('end', null);
      };

      self.resetLabel = function () {
          self.resetNode();
          self.selectedLabel = null;
          self.nodeExamples = [];

          // Reset the query parameter
          $location.search('label', null);
      };

      self.loadDependencies = function() {
        $location.search('day', self.selectedDay);
        $location.search('old', self.includeOldNodes);

        self.dependenciesLoading = true;
        self.dependencies = {};
        self.legend = {};

          dependenciesService.getNodeDependencies(self.team.id, self.selectedLabel, self.selectedNode, self.selectedDay, false, self.includeOldNodes).then(function (response) {
            var data = response.data;
            var dependencies = data.dependencies;

            // Get periods about the main node
            for ( var i in dependencies ) {
                if ( i == self.selectedLabel ) {
                    for ( var j in dependencies[i] ) {
                        if ( dependencies[i][j].name == self.selectedNode ) {

                            // Remove the node
                            self.nodeProperties = dependencies[i][j];
                            dependencies[i].splice(j, 1);

                            // If there is no node in this label, remove it too
                            if ( dependencies[i].length == 0 ) {
                                delete dependencies[i]
                            }
                            break;
                        }
                    }
                }
            }

            // Create the legend
            var labels = Object.keys(dependencies);
            var colorHash = new ColorHash();
            for ( var i in labels) {
                self.legend[labels[i]] = colorHash.hex(labels[i]);
            }

            // Add the current node in the legends
            self.legend[self.selectedLabel] = colorHash.hex(self.selectedLabel);

            // Create the Vis.js graph
            self.graph = config.graph_schema(data.graph.nodes, data.graph.relationships);

            // Reformat the dependencies, associate their rule and their relationship
            for (var label in dependencies) {
                for (var i in self.labels) {
                    if (self.labels[i]['name'] == label) {
                        self.dependencies[label] = {
                            'nodes': dependencies[label],
                            'rule': self.labels[i]['qos_query']
                        }
                    }
                }
            }

            self.dependenciesLoading = false;
        });
      };

      self.selectNode = function (node) {
          $location.search('node', node);
          self.selectedNode = node;
          self.loadDependencies();

      };

      self.hasDependencies = function () {
          return Object.keys(self.dependencies).length > 0;
      }

      self.getNodeDate = function(d) {
          if (!d) {
            return '--'
          }
          return $filter('date')(d * 1000, 'yyyy-MM-dd HH:mm:ss')
      }

      self.displayRelationshipPeriods = function(periods) {
        modalService.relationshipPeriods(periods);
      };


      self.deleteNode = function(label, node) {
        $confirm({
            text: 'Are you sure you want to delete the node "' + node + '" ?',
            title: 'Delete node',
            ok: 'Yes',
            cancel: 'No'
        })
        .then(function() {
            dependenciesService.deleteNode(self.team.id, label, node).then(function(response) {
                toastr.success('The node ' + node + ' has been deleted.');
                self.init();
                self.resetLabel();
            }, function(err) {

              // Node has still dependencies
              if ( err.status == 409 ) {
                $confirm({
                    text: 'Node "' + node + '" has still dependencies, do you want to delete them all ?',
                    title: 'Delete node and relationships',
                    ok: 'Yes',
                    cancel: 'No'
                })
                .then(function() {
                  dependenciesService.deleteNode(self.team.id, label, node, true).then(function(response) {
                      toastr.success('The node ' + node + ' and its relationships have been deleted.');
                      self.init();
                      self.resetLabel();
                  });
                });
              }
            });
        });
      }

  });
