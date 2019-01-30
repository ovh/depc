'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:DependenciesCtrl
 * @description
 * # DependenciesCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('DependenciesCtrl', function ($routeParams, $location, $interval, $q, $confirm, toastr, config, modalService, teamsService, dependenciesService, rulesService) {
    var self = this;
    self.teamName = $routeParams.team;

    self.selectedLabel = null;
    self.selectedNode = null;
    self.loadNodes = false;

    self.resultTitle = null;
    self.nodeSearched = null;
    self.nodesResult = [];

    self.graph = null;
    self.legend = {};
    self.dependenciesLoading = false;
    self.dependencies = {
        'isMonitored': {},
        'isNotMonitored': {}
    };

      // Dates range
      self.date = {
          startDate: moment().startOf("day"),
          endDate: moment().endOf("day")
      };

      self.init = function () {
          self.labels = [];
          self.rules = [];
          self.labelsLoading = true;

          teamsService.getTeamByName(self.teamName).then(function (response) {
              self.team = response.data;

              dependenciesService.getTeamLabels(self.team.id).then(function (response) {
                  self.labels = response.data;
                  self.labelsLoading = false;
                  // Handle the query parameters
                  if ($routeParams.start) {
                      self.date.startDate = moment.unix($routeParams.start);
                  }

                  if ($routeParams.end) {
                      self.date.endDate = moment.unix($routeParams.end);
                  }

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

      self.getRuleDetailsUrl = function (rule_name, name) {
          var start = moment(self.date.startDate).unix();
          var end = moment(self.date.endDate).unix();

          return '#/teams/' + self.teamName + '/rules?rule=' + rule_name + '&name=' + name + '&start=' + start + '&end=' + end + '&exec=1';
      };
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
          self.dependencies = {
              'isMonitored': {},
              'isNotMonitored': {}
          };
          self.allResults = null;
          self.dependenciesStatus = {};

          // Reset the query parameters
          $location.search('node', null);
          $location.search('start', null);
          $location.search('end', null);
          $location.search('exec', null);
      };

      self.resetLabel = function () {
          self.resetNode();
          self.selectedLabel = null;
          self.nodeExamples = [];

          // Reset the query parameter
          $location.search('label', null);
      };

      self.selectNode = function (node) {
          $location.search('node', node);
          self.selectedNode = node;
          self.dependenciesLoading = true;

          dependenciesService.getNodeDependencies(self.team.id, self.selectedLabel, self.selectedNode, false).then(function (response) {
              var data = response.data;
              var dependencies = data.dependencies;

              // contain label with special color
              var colorArgs = new Object();

              // Create the legend
              var colorHash = new ColorHash();

              for (var i in self.labels) {
                  var index = Object.keys(dependencies).indexOf(self.labels[i].name);

                  if ( index > -1 ) {
                    if (self.labels[i].color == null) {
                        self.legend[self.labels[i].name] = colorHash.hex(self.labels[i].name);
                    } else {
                        self.legend[self.labels[i].name] = self.labels[i].color;
                        colorArgs[self.labels[i].name] = self.labels[i].color;
                    }
                  }
              }
              // Create the graph
              self.graph = config.graph_schema(data.graph.nodes, data.graph.relationships, colorArgs);

              // Group the dependencies by Monitored ones or not
              for (var label in dependencies) {
                  for (var i in self.labels) {
                      if (self.labels[i]['name'] == label) {
                        self.dependencies['isMonitored'][label] = {
                            'nodes': dependencies[label],
                            'rule': self.labels[i]['rule']
                        }
                      }
                  }
              }

              self.dependenciesLoading = false;

              // Launch the rules
              if ($routeParams.exec === '1') {
                  self.launchRules();
              }
          });
      };

      self.hasMonitoredLabel = function () {
          return Object.keys(self.dependencies.isMonitored).length > 0;
      }

      self.deleteNode = function(node) {
        $confirm({
            text: 'Are you sure you want to delete the node "' + node.name + '" ?',
            title: 'Delete node',
            ok: 'Yes',
            cancel: 'No'
        })
        .then(function() {
            dependenciesService.deleteNode(self.team.id, self.selectedLabel, node.name).then(function(response) {
                toastr.success('The node ' + node.name + ' has been deleted.');
                self.init();
                self.resetLabel();
            }, function(err) {

              // Node has still dependencies
              if ( err.status == 409 ) {
                $confirm({
                    text: 'Node "' + node.name + '" has still dependencies, do you want to delete them all ?',
                    title: 'Delete node and relationships',
                    ok: 'Yes',
                    cancel: 'No'
                })
                .then(function() {
                  dependenciesService.deleteNode(self.team.id, self.selectedLabel, node.name, true).then(function(response) {
                      toastr.success('The node ' + node.name + ' and its relationships have been deleted.');
                      self.init();
                      self.resetLabel();
                  });
                });
              }
            });
        });
      }

  });
