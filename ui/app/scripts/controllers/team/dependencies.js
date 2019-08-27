'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:DependenciesCtrl
 * @description
 * # DependenciesCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('DependenciesCtrl', function ($routeParams, $location, $filter, $confirm, $q, toastr, config, modalService, teamsService, dependenciesService, FileSaver, Blob) {
    var self = this;
    self.teamName = $routeParams.team;

    self.directRelationshipsCollapsed = false;
    self.impactedNodesCollapsed = false;

    self.selectedLabel = null;
    self.selectedNode = null;
    self.nodeProperties = {};
    self.loadNodes = false;
    self.includeInactive = false;
    self.displayImpactedNodes = false;
    self.selectedDay = moment().format('YYYY-MM-DD');

    self.resultTitle = null;
    self.nodeSearched = null;
    self.nodesResult = [];

    self.graph = null;
    self.legend = {};
    self.dependenciesLoading = false;
    self.dependencies = {};

    self.impactedFirstLoadDone = false;
    self.impactedLabel = null;
    self.impactedTimeFormat = moment().format('HH:mm:ss');
    self.impactedDatetime = moment(self.impactedTimeFormat, 'HH:mm:ss');
    self.impactedNodesLoading = false;
    self.impactedNodes = [];
    self.impactedCurrentPage = 1;
    self.impactedTotalNumberOfNodes = 0;
    self.impactedDefaultLimit = 25;
    self.impactedDownloadInProgress = false;
    self.impactedDownloadInProgressWithoutInactive = false;
    self.impactedDownloadInProgressWithInactive = false;

      self.init = function () {
          self.labels = [];
          self.labelsLoading = true;

          if ($routeParams.day) {
            self.selectedDay = $routeParams.day;
          }

          if ($routeParams.time) {
            self.impactedTimeFormat = $routeParams.time;
            self.impactedDatetime = moment(self.impactedTimeFormat, 'HH:mm:ss');
          }

          if ($routeParams.inactive) {
            self.includeInactive = true;
          }

          if ($routeParams.impacted) {
            self.displayImpactedNodes = true;
          }

          teamsService.getTeamByName(self.teamName).then(function (response) {
              self.team = response.data;

              dependenciesService.getTeamLabels(self.team.id).then(function (response) {
                  self.labels = response.data;
                  self.labelsLoading = false;

                  if ($routeParams.impactedLabel) {
                    self.impactedLabel = $routeParams.impactedLabel;
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

      self.refreshAll = function() {
        if (!self.selectedLabel || !self.selectedNode) {
          return
        }

        self.loadDependencies();
        self.refreshImpactedNodes();
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
              self.loadNodes = false;
          });
      };

      // Search nodes by their name
      self.searchNode = function () {
          if ( !self.nodeSearched ) { return; }
          self.loadNodes = true;
          self.selectedNode = null;
          self.nodesResult = [];
          self.resultTitle = null;

          // Try to find the node with the exact same name
          dependenciesService.getTeamLabelNode(self.team.id, self.selectedLabel, self.nodeSearched).then(function (response) {
            self.selectNode(response.data.name);
            self.loadNodes = false;
          }).catch(function(e) {

              // Find nodes using pattern
              dependenciesService.getTeamLabelNodes(self.team.id, self.selectedLabel, self.nodeSearched).then(function (response) {
                self.nodesResult = response.data;

                if ( self.nodesResult.length > 0 ) {
                    self.resultTitle = 'Node not found, but got ' + self.nodesResult.length + ' node(s) containing "' + self.nodeSearched + '".';
                } else {
                    self.resultTitle = 'Node not found.';
                }

                self.loadNodes = false;
              });
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
        if ( self.includeInactive ) {
            $location.search('inactive', true);
        } else {
            $location.search('inactive', null);
        }

        if ( self.displayImpactedNodes ) {
            $location.search('impacted', true);
        } else {
            $location.search('impacted', null);
        }

        self.dependenciesLoading = true;
        self.dependencies = {};
        self.legend = {};

          dependenciesService.getNodeDependencies(self.team.id, self.selectedLabel, self.selectedNode, self.selectedDay, false, self.includeInactive, self.displayImpactedNodes).then(function (response) {
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
          self.refreshAll();
      };

      self.hasDependencies = function () {
          return Object.keys(self.dependencies).length > 0;
      }

      self.hasImpactedNodes = function () {
        return self.impactedNodes.length > 0;
      };

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

      self.refreshImpactedNodes = function() {
        if (!self.impactedLabel || !self.impactedDatetime || !self.selectedDay) {
          return
        }

        self.impactedTimeFormat = moment(self.impactedDatetime).format('HH:mm:ss');

        $location.search('impactedLabel', self.impactedLabel);
        $location.search('time', self.impactedTimeFormat);

        self.impactedNodesLoading = true;
        self.impactedCurrentPage = 1;
        self.impactedTotalNumberOfNodes = 0;

        dependenciesService.getTeamImpactedNodesCount(self.team.id, self.selectedLabel, self.selectedNode, self.impactedLabel).then(function(response) {
          self.impactedTotalNumberOfNodes = response.data.count;
          self.getImpactedNodes(self.impactedCurrentPage);
        });
      };

      self.getImpactedNodes = function(page) {
        self.impactedNodesLoading = true;
        var skip = (page - 1) * self.impactedDefaultLimit;
        var impactedDateUnix = moment(self.selectedDay + ' ' + self.impactedTimeFormat, "YYYY-MM-DD HH:mm:ss").unix();

        dependenciesService.getTeamImpactedNodes(self.team.id, self.selectedLabel, self.selectedNode, self.impactedLabel, skip, self.impactedDefaultLimit, impactedDateUnix).then(function(response) {
          self.impactedNodes = response.data;
          self.impactedNodesLoading = false;
          self.impactedFirstLoadDone = true;
        });
      };

      self.extractAllImpactedNodes = function(inactive) {
        self.impactedDownloadInProgress = true;
        if (inactive) {
          self.impactedDownloadInProgressWithInactive = true;
        } else  {
          self.impactedDownloadInProgressWithoutInactive = true;
        }
        var impactedDateUnix = moment(self.selectedDay + ' ' + self.impactedTimeFormat, "YYYY-MM-DD HH:mm:ss").unix();

        dependenciesService.getTeamImpactedNodesAll(self.team.id, self.selectedLabel, self.selectedNode, self.impactedLabel, impactedDateUnix, inactive).then(function(response) {
          var allImpactedNodesString = response.data['data'];

          var filename = 'impacted_' + self.impactedLabel + '_list';
          if (inactive) {
            filename += '_with_inactive';
          }
          filename += '.json';

          var downloadData = new Blob([allImpactedNodesString], { type: 'text/plain;charset=utf-8' });
          FileSaver.saveAs(downloadData, filename);

          self.impactedDownloadInProgress = false;
          self.impactedDownloadInProgressWithInactive = false;
          self.impactedDownloadInProgressWithoutInactive = false;
        });
      };
  });
