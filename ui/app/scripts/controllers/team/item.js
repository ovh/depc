'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ItemCtrl
 * @description
 * # ItemCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ItemCtrl', function ($rootScope, $scope, $routeParams, qosService, teamsService, configurationsService, rulesService, chartsService, dependenciesService, config) {
   var self = this;

    self.teamName = $routeParams.team;
    self.label = $routeParams.label;
    self.name = $routeParams.name;
    self.loading = true;
    self.getSlideBg = config.getSlideBg;

    self.qosQuery = {'type': null};
    self.dependenciesQos = {};

    teamsService.getTeamByName(self.teamName).then(function(response) {
        self.team = response.data;

        $scope.$watch(function() {
            return $rootScope.globals.date;
        }, function() {
            self.loading = true;
            self.fetchData();
        }, true);

        self.fetchData = function() {
            // Parse the configuration for this label
            configurationsService.getTeamCurrentConfiguration(self.team.id).then(function(response) {
                self.currentConfig = response.data.data;
                var label_config = self.currentConfig[self.label];

                if ( label_config == undefined ) {
                    self.qosQuery = null;
                    return;
                }

                if ( label_config['qos'].startsWith('rule') ) {
                    self.qosQuery.type = 'rule';

                    // Get the rule's name
                    var regex = /^rule.(.+)$/g;
                    var match = regex.exec(label_config['qos']);
                    var rule = match[1];

                    // Just in case the rule contains spaces
                    if ( rule.startsWith('\'') ) {
                      rule = rule.substring(1, rule.length-1);
                    }

                    rulesService.getTeamRules(self.team.id).then(function(response) {
                        var rules = response.data.rules;
                        for ( var i in rules ) {
                            if ( rules[i].name == rule ) {
                                self.rule = rules[i];
                            }
                        }
                    });

                } else {
                    self.qosQuery.type = 'dependencies';

                    // First we check the number of dependencies
                    dependenciesService.countNodeDependencies(self.team.id, self.label, self.name).then(function(response) {
                        var count = response['data']['count'];
                        self.dependenciesCount = count;

                        // Get the node's dependencies declared in the configuration
                        dependenciesService.getNodeDependencies(self.team.id, self.label, self.name, true).then(function(response) {
                            var dependencies = response['data']['dependencies'];
                            self.graph = config.graph_schema(response.data.graph.nodes, response.data.graph.relationships, null);

                            self.dependencies = [];

                            for ( var label in dependencies ) {

                                for ( var node in dependencies[label]) {

                                    // Do not register itself
                                    var dep = dependencies[label][node];
                                    if ( label != self.label || dep['name'] != self.name ) {
                                        dep['label'] = label;
                                        self.dependencies.push(dep);
                                        self.dependenciesQos[dep['name'] + '-' + dep['label']] = {
                                            'name': dep['name'],
                                            'label': dep['label'],
                                            'chart': 'loading'
                                        };
                                        self.computeDependencyQOS(dep['name'], dep['label']);
                                    }
                                }
                            }
                        });
                    });
                }

                // Get the QOS evolution of the main item
                var click_fn = function () {
                    self.ruleDate = Highcharts.dateFormat('%d-%m-%Y', this.x);
                    $rootScope.$apply();
                };
                var lineChart = chartsService.getChartLine(null, null, null, 320, null, null, null, null, click_fn);
                lineChart.series[0].data = [];
                self.average = 0;
                self.warnings = 0;
                self.errors = 0;

                var start = $rootScope.globals.start;
                var end = $rootScope.globals.end;

                // Fetch the datapoints
                qosService.getTeamItemQos(start, end, self.team.id, self.label, self.name).then(function(response) {
                    var dps = response.data;

                    // The QoS is unknown for this month
                    if ( config.isEmpty(dps) ) {
                        self.average = 'unknown';
                        self.loading = false;
                        return;
                    }

                    var total = 0;

                    for (var i in dps) {
                        var date = moment.unix(i).toDate();
                        var value = dps[i];
                        total += value;

                        if ( value < config.getThresholds('error') ) {
                            self.errors += 1;
                        } else if ( value < config.getThresholds('warning') ) {
                            self.warnings += 1;
                        }

                        // Create the chart view
                        lineChart.series[0].data.push([i * 1000, value]);
                    }

                    self.lineChart = lineChart;

                    // Total average for the current month
                    self.average = total / Object.keys(dps).length;
                    self.loading = false;
                });
            });
        }
    });

    self.computeDependencyQOS = function(name, label) {
        var lineChart = chartsService.getChartLine(null, null, null, 150, null, null, null, null, null);

        var start = $rootScope.globals.start;
        var end = $rootScope.globals.end;
        var total = 0;

        // Get the QOS evolution of the dependencies
        qosService.getTeamItemQos(start, end, self.team.id, label, name).then(function(response) {
            var dps = response.data;

            // The QoS is unknown for this month
            if ( !config.isEmpty(dps) ) {
                for (var i in dps) {
                    var date = moment.unix(i).toDate();
                    var value = dps[i];
                    total += value;

                    lineChart.series[0].data.push([i * 1000, value]);
                }
                self.dependenciesQos[name + '-' + label]['chart'] = {
                    'dps': lineChart,
                    'average': total / Object.keys(dps).length
                };
            } else {
                self.dependenciesQos[name + '-' + label]['chart'] = null;
            }
        });
    };

    self.getDayBg = function(count, type) {
        var bg = 'bg-unknown';
        if ( parseFloat(count) > 0 && type == 'warn' ) {
            bg = 'bg-warning';
        } else if ( parseFloat(count) > 0 && type == 'crit' ) {
            bg = 'bg-error';
        }
        return bg;
    };

    self.getRuleDetailsUrl = function () {
      if ( self.rule == undefined ) {
        return;
      }
      var date = moment.utc(self.ruleDate, 'DD-MM-YYYY');
      var start = date.startOf("day").unix();
      var end = date.endOf("day").unix();

      return '#/teams/' + self.teamName + '/rules?rule=' + self.rule.name + '&name=' + self.name + '&start=' + start + '&end=' + end + '&exec=1';
    };

});