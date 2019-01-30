'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ConfigurationCtrl
 * @description
 * # ConfigurationCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ConfigurationCtrl', function ($routeParams, config, modalService, teamsService, configurationsService) {
    var self = this;

    self.teamName = $routeParams.team;

    self.currentConfig = null;
    self.currentJsonConfig = null;
    self.loadingCurrentConfig = true;

    self.configs = [];
    self.loadingConfigs = true;

    self.cmOption = {
      lineNumbers: false,
      theme: 'twilight',
      mode: 'javascript',
      readOnly: true
    };

    teamsService.getTeamByName(self.teamName).then(function(response) {
      self.team = response.data;

      self.loadConfigs = function() {
      self.loadingCurrentConfig = true;
      self.loadingConfigs = true;

          configurationsService.getTeamConfigurations(self.team.id).then(function(response) {
              self.configs = response.data;

              if ( self.configs.length > 0 ) {
                  configurationsService.getTeamCurrentConfiguration(self.team.id).then(function(response) {
                      self.currentConfig = response.data;

                      // Construct the graph
                      var nodes = [];
                      var edges = [];
                      var color = {
                        'rule': '#d2ead3',
                        'operation': '#f4cccc',
                        'aggregation': '#c9daf8'
                      };

                      for ( var label in self.currentConfig.data ) {
                        var qos_query = self.currentConfig.data[label]['qos'];
                        if ( qos_query.startsWith('rule') ) {
                          var regex = /^rule.(.+)$/g;
                          var match = regex.exec(qos_query);
                          var rule = match[1];

                          // Just in case the rule contains spaces
                          if ( rule.startsWith('\'') ) {
                            rule = rule.substring(1, rule.length-1);
                          }

                          nodes.push({
                            id: label,
                            font: { multi: 'html' },
                            margin: { top: 10, right: 10, bottom: 10, left: 10 },
                            widthConstraint: { minimum: 80, maximum: 200 },
                            label: label + '\n<b>' + rule + '</b>',
                            shape: 'box',
                            color: color['rule']
                          })
                        } else {
                          var regex = /^(operation|aggregation)[.](.+)(\[.+\])$/g;
                          var match = regex.exec(qos_query);

                          nodes.push({
                            id: label,
                            font: { multi: 'html' },
                            margin: { top: 10, right: 10, bottom: 10, left: 10 },
                            widthConstraint: { minimum: 80, maximum: 200 },
                            label: label + '\n<b>' + match[2] + '</b>',
                            shape: 'box',
                            color: color[match[1]]
                          })

                          var deps = match[3].substring(1, match[3].length-1).split(', ');
                          for ( var i in deps ) {
                            edges.push({
                              from: label,
                              to: deps[i]
                            })
                          }
                        }
                      }

                      self.graph = config.getConfigGraph(nodes, edges);

                      self.currentJsonConfig = JSON.stringify(self.currentConfig.data, null, ' ');
                      self.loadingCurrentConfig = false;
                  });
              }
              self.loadingConfigs = false;
          });
        };
        self.loadConfigs();
    });

    self.isCurrentConfig = function(config) {
    if ( !self.currentConfig ) {
      return false;
    }
    return config.id == self.currentConfig.id;
    };

    self.displayConfig = function(config) {
      modalService.displayConfig(self.team, config).result.then(function(data) {
        self.loadConfigs();
      }, function() {});
    };

    self.newConfig = function() {
      var placeholder = {
       "Server": {
        "qos": "rule.Servers"
       },
       "Cluster": {
        "qos": "operation.AND[Server]"
       }
      };

      // We take the last config as the placeholder
      if ( self.currentConfig != null ) {
        placeholder = self.currentConfig.data;
      }

      modalService.newConfig(self.team, placeholder).result.then(function(data) {
       self.loadConfigs();
      }, function() {});
    };
  });