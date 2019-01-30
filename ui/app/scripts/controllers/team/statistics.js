'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:StatisticsCtrl
 * @description
 * # StatisticsCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('StatisticsCtrl', function ($rootScope, $scope, $routeParams, teamsService, chartsService, statisticsService) {
    var self = this;

    self.teamName = $routeParams.team;

    self.human_types = {
      'total': 'Total number of nodes',
      'qos': 'Nodes with a QOS',
      'noqos': 'Nodes without QOS',
      'time': 'Time'
    }

    self.fetchStatistics = function() {

      // Remove existing series
      self.types = {};
      self.selectedType = null;
      self.typeChart = chartsService.getSimpleChart();
      self.typeLoading = true;

      self.labels = {};
      self.selectedLabel = null;
      self.labelChart = chartsService.getSimpleChart();
      self.labelLoading = true;

      teamsService.getTeamByName(self.teamName).then(function(response) {
        self.team = response.data;

        var date = moment($rootScope.globals.date);
        var start = date.startOf('month').format('X');
        var end = date.endOf('month').format('X');

        self.labelLoading = true;
        statisticsService.getTeamStatistics(self.team.id, 'label', start, end).then(function(response) {
          var labels = response.data;

          for ( var label in labels ) {
            self.labels[label] = {};

            for ( var type in labels[label] ) {
              // The time statistics is not useful for the user
              if ( type == 'time' ) {
                continue;
              }
              var values = [];
              for ( var ts in labels[label][type] ) {
                var qos = labels[label][type][ts];
                values.push([ts * 1000, qos]);
              }
              self.labels[label][type] = values;
            }
          };
          self.labelLoading = false;

          // If at least a label exists, we select it
          if ( Object.keys(self.labels).length > 0 ) {
            self.selectedLabel = Object.keys(self.labels)[0];
            self.updateLabelChart();
          }
        });

        // Humm.. yes, there's some repetition here...
        self.typeLoading = true;
        statisticsService.getTeamStatistics(self.team.id, 'type', start, end).then(function(response) {
          var types = response.data;

          for ( var type in types ) {
            if ( type == 'time' ) {
              continue;
            }
            self.types[type] = {};

            for ( var label in types[type] ) {
              var values = [];
              for ( var ts in types[type][label] ) {
                var qos = types[type][label][ts];
                values.push([ts * 1000, qos]);
              }
              self.types[type][label] = values;
            }
          };

          // By default we select the Total statistics
          self.selectedType = 'total';
          self.updateTypeChart();
          self.typeLoading = false;
        });
      });
    };

    self.updateLabelChart = function() {
      var types = self.labels[self.selectedLabel];
      var series = [];
      for ( var type in types ) {
        series.push({
          name: self.human_types[type],
          data: types[type],
          dataGrouping: {
              enabled: false
          }
        });
      }
      self.labelChart['series'] = series;
    };

    self.updateTypeChart = function() {
      var labels = self.types[self.selectedType];
      var series = [];
      for ( var label in labels ) {
        series.push({
          name: label,
          data: labels[label],
          dataGrouping: {
              enabled: false
          }
        });
      }
      self.typeChart['series'] = series;
    };

    self.hasStatistics = function() {
      if ( Object.keys(self.labels).length > 0 ) {
        return true;
      }
      return false;
    }

    $scope.$watch(function() {
      return $rootScope.globals.date;
    }, function() {
        self.fetchStatistics();
    }, true);


  });