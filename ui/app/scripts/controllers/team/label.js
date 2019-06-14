'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:LabelCtrl
 * @description
 * # LabelCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('LabelCtrl', function ($rootScope, $scope, $timeout, $routeParams, $location, teamsService, qosService, dependenciesService, chartsService, config) {
   var self = this;

   self.teamName = $routeParams.team;
   self.label = $routeParams.label;
   self.nodes = [];
   self.search = null;
   self.items = [];
   self.getSlideBg = config.getSlideBg;
   self.selectedWorstDay = null;
   self.worstLoading = true;

   teamsService.getTeamByName(self.teamName).then(function(response) {
        self.team = response.data;

        $scope.$watch(function() {
          return $rootScope.globals.date;
        }, function() {
            self.launchLabelCompute();
            self.computeWorstInfra();
        }, true);
    });

    // Get the worst items for this label
    self.computeWorstInfra = function(date) {
      self.worstLoading = true;
        if ( !date ) {
          date = moment().add(-1, 'days').format('YYYY-MM-DD');
        }
        self.selectedWorstDay = date;

        self.items = [];
        qosService.getTeamWorstItemQos(self.team.id, self.label, date).then(function(response) {
            self.items = response.data;
            $timeout(function(){
              $rootScope.$apply();
              self.worstLoading = false;
            });
        });
    };

   var click_fn = function () {
        var date = Highcharts.dateFormat('%Y-%m-%d', this.x);
        self.computeWorstInfra(date);
    };

    // Compute the customers QoS for each period
    self.computeInfraQos = function(period, start, end, loop) {
      qosService.getTeamLabelQos(start, end, self.team.id, self.label).then(function(response) {
        var dps = response.data;
        var data = [];
        var total = 0;
        var warnings = 0;
        var errors = 0;

        if ( Object.keys(dps).length > 0 ) {
          for ( var i in dps ) {
            var value = dps[i];
            data.push([i * 1000, value]);

            // Number of warning and critical days
            if ( value < config.getThresholds('error') ) {
              errors += 1;
            } else if ( value < config.getThresholds('warning') ) {
              warnings += 1;
            }
            total += value;
          }

          self.periods[period]['average'] = total / data.length;
          self.periods[period]['warnings'] = warnings;
          self.periods[period]['errors'] = errors;

          // Selected period is bigger
          var height = 200;
          if ( loop == 0 ) {
            height = 270;
          }

          var html = '<span style="color:{point.color}">\u25CF</span> {point.y}%';

          var lineChart = chartsService.getChartLine(null, null, null, height, null, null, null, html, click_fn);
          lineChart.series[0].data = data;
          self.periods[period]['chart'] = lineChart;

        // No datapoints for this period
        } else {
          delete self.periods[period];
        }
      });
    };

    // Loop on wanted number of periods
    self.launchLabelCompute = function() {
      var date = moment($rootScope.globals.date);  // object copy
      var start_o = moment.unix($rootScope.globals.start);
      var end_o = moment.unix($rootScope.globals.end);

      self.periods = {};

      for ( var i=0; i<config.monthsHistoryCount(); i++ ) {

        // Substract 1 month in each iteration
        if ( $rootScope.globals.view == 'month' ) {
          var start = date.startOf('month').format('X');
          var end = date.endOf('month').format('X');
          var period = date.format('MMMM YYYY');
          date = date.subtract(1, 'months');
        }

        // Substract the period between from & to in each iteration
        else {
          var start = start_o.startOf('day').format('X');
          var end = end_o.endOf('day').format('X');
          var period = start_o.format('YYYY-MM-DD') + ' → ' + end_o.format('YYYY-MM-DD');

          // Decrement the period
          var count = end_o.diff(start_o, 'days');
          end_o = moment(start_o.subtract(1, 'days'));
          start_o = moment(start_o.subtract(count, 'days'));
        }

        self.periods[period] = {
          'month': period,
          'chart': null,
          'warnings': 0,
          'errors': 0
        };
        self.computeInfraQos(period, start, end, i);
      }
    };

    // Search nodes by their name
    self.searchNode = function () {
        if ( !self.nodeSearched ) { return; }
        self.loadNodes = true;
        self.selectedNode = null;
        self.nodesResult = [];
        self.resultTitle = null;

        // Try to find the node with the exact same name
        dependenciesService.getTeamLabelNode(self.team.id, self.label, self.nodeSearched).then(function (response) {
          self.loadNodes = false;
          $location.path( "/teams/" + self.teamName + "/dashboard/" + self.label + "/" + self.nodeSearched );
        }).catch(function(e) {

            // Find nodes using pattern
            dependenciesService.getTeamLabelNodes(self.team.id, self.label, self.nodeSearched).then(function (response) {
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

    // Fetch some nodes as examples for the user
    self.loadExamples = function () {
      self.loadNodes = true;
      self.selectedNode = null;
      self.nodesResult = [];
      self.resultTitle = null;
      dependenciesService.getTeamLabelNodes(self.team.id, self.label, null, 10, true).then(function (response) {
          self.nodesResult = response.data;
          self.loadNodes = false;
      });
  };

    self.getStateByQos = function(qos) {
      return config.getStateByQos(qos);
    };

    self.getLabelClassByQos = function(qos) {
      return config.getLabelClassByQos(qos);
    };
});