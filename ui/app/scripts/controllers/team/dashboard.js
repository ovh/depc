'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:DashboardCtrl
 * @description
 * # DashboardCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('DashboardCtrl', function ($rootScope, $scope, $timeout, $filter, $interval, $anchorScroll, $location, $routeParams, teamsService, qosService, chartsService) {
    var self = this;

    self.teamName = $routeParams.team;
    self.chartLoading = true;
    self.isFirstDayOfTheMonth = false;
    self.previousMonth = moment().subtract(1, 'months').format('MMMM YYYY');

    self.goToPreviousMonth = function() {
        $rootScope.globals.date.add(-1, 'months');
        $location.search('m', $rootScope.globals.date.format('MM-YYYY'));
    };

    teamsService.getTeamByName(self.teamName).then(function(response) {
        self.team = response.data;

        self.computeInfraQos = function() {
            self.infra = [];

            var date = moment($rootScope.globals.date);
            var now = moment();
            self.isFirstDayOfTheMonth = (now.format('YYYYMM') === date.format('YYYYMM') && now.date() === 1);

            if (self.isFirstDayOfTheMonth) {
                return;
            }

            self.chartLoading = true;

            var start = $rootScope.globals.start;
            var end = $rootScope.globals.end;

            qosService.getTeamQos(start, end, self.team.id).then(function(response) {
                var labels = response.data;
                for ( var i in labels ) {
                    var values = [];
                    var total = 0;
                    for ( var ts in labels[i] ) {
                        var qos = labels[i][ts];

                        // Add the day in the chart
                        values.push([ts * 1000, qos]);

                        // Update the average for the month
                        total += qos;
                    }

                    if ( values.length == 0 )  {
                        continue;
                    };

                    var last = values[values.length - 1][1];

                    var before_last = last;
                    if ( values.length > 1 ) {
                        before_last = values[values.length - 2][1];
                    }

                    var lineChart = chartsService.getChartLine(null, null, null, 200, null);
                    lineChart.series[0].data = values;


                    var average = null;
                    if ( values.length !==  0 ) {
                        average = total / values.length;
                    }

                    var rounded_last = $filter('numberTrunc')(last, 3);
                    var rounded_before_last = $filter('numberTrunc')(before_last, 3);
                    self.infra.push({
                        'name': i,
                        'type': 'label',
                        'chart': lineChart,
                        'trend': $filter('numberTrunc')(rounded_last - rounded_before_last, 3),
                        'last': rounded_last,
                        'before_last': rounded_before_last,
                        'average': $filter('numberTrunc')(average, 3),
                    });
                }

                self.totalNodesCount = self.infra.length;
                self.finished();
            });
        };

        $scope.$watch(function() {
          return $rootScope.globals.date;
        }, function() {
            self.computeInfraQos();
        }, true);
    });

    self.finished = function() {
        if ( self.infra.length == self.totalNodesCount ) {
            var summaryTables = [[], [], []];
            var cpt = 0;
            for ( var i in self.infra ) {
                summaryTables[cpt].push(self.infra[i]);
                cpt += 1;
                if ( cpt == 3 ) {
                    cpt = 0;
                }
            }
            self.summaryTables = summaryTables;
            self.chartLoading = false;
            self.go($location.hash());
        }
    };

    self.computeNodeQos = function(label, name) {
        var start = $rootScope.globals.start;
        var end = $rootScope.globals.end;

        qosService.getTeamItemQos(start, end, self.team.id, label, name).then(function(response) {
            var dps = response.data;

            var values = [];
            var total = 0;
            for ( var ts in dps ) {
                var qos = dps[ts];

                // Add the day in the chart
                values.push([ts * 1000, qos]);

                // Update the average for the month
                total += qos;
            }

            var last = values[values.length - 1][1];

            var before_last = last;
            if ( values.length > 1 ) {
                before_last = values[values.length - 2][1];
            }

            var lineChart = chartsService.getChartLine(null, null, null, 200, null);
            lineChart.series[0].data = values;


            var average = null;
            if ( values.length !==  0 ) {
                average = total / values.length;
            }

            var rounded_last = $filter('numberTrunc')(last, 3);
            var rounded_before_last = $filter('numberTrunc')(before_last, 3);
            self.infra.push({
                'name': name,
                'label': label,
                'type': 'node',
                'chart': lineChart,
                'trend': $filter('numberTrunc')(rounded_last - rounded_before_last, 3),
                'last': rounded_last,
                'before_last': rounded_before_last,
                'average': $filter('numberTrunc')(average, 3)
            });
        });
    }

    self.getTrendIconClass = function(trend) {
        if ( trend > 0 ) {
            return 'glyphicon-arrow-up';
        } else if ( trend < 0 ) {
            return 'glyphicon-arrow-down';
        }

        return '';
    }

    self.getTrendClass = function(trend) {
        if ( trend > 0 ) {
            return 'text-success';
        } else if ( trend < 0 ) {
            return 'text-error';
        }
        return '';
    }

    self.getTrendClassForSummary = function(trend) {
        if ( trend > 0 ) {
            return 'custom-success';
        } else if ( trend < 0 ) {
            return 'custom-danger';
        }
        return '';
    }

    self.getQosPanelClass = function(name) {
        if ( !$location.hash() ) {
            return '';
        }

        if ( $location.hash() == name ) {
            return 'active';
        } else {
            return 'inactive';
        }
    };

    self.go = function(name) {
        if ($location.hash() !== name) {
            $location.hash(name);
        } else {
            $anchorScroll();
            var everywhere = angular.element(window.document);
            everywhere.bind('click', function(event){
                var elt = event.target;
                if ( elt.closest('.table-summary') == null && elt.closest('.active') == null && $location.hash() != '' ) {
                    $location.hash('');
                    $rootScope.$apply();
                }
            });
        }
    };
  });
