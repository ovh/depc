'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:NavbarCtrl
 * @description
 * # NavbarCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('NavbarCtrl', function ($rootScope, $scope, $location, $routeParams, $route) {

    var updateMonth = function() {
      $rootScope.globals.view = 'month';
      var date = moment($rootScope.globals.date);
      $rootScope.globals.start = date.startOf('month').format('X');
      $rootScope.globals.end = date.endOf('month').format('X');
      $location.search('f', null);
      $location.search('t', null);
    };

    $scope.currentMonth = function(change_url) {
      $rootScope.globals.date = moment.utc();
      if ( change_url ) {
        $location.search('m', $rootScope.globals.date.format('MM-YYYY'));
      }
      updateMonth();
    };

    $scope.incMonth = function() {
      $rootScope.globals.date.add(1, 'months');
      $location.search('m', $rootScope.globals.date.format('MM-YYYY'));
      updateMonth();
    };

    $scope.decMonth = function() {
      $rootScope.globals.date.add(-1, 'months');
      $location.search('m', $rootScope.globals.date.format('MM-YYYY'));
      updateMonth();
    };

    // Handle the month view
    if ( $route.current.params.m != undefined ) {
      // We add 15 days (arbitrary) to select the middle of the wanted month
      $rootScope.globals.date = moment($route.current.params.m, "MM-YYYY").utc().add(15, 'days');
      updateMonth();

    // Handle the custom view
    } else if ( $route.current.params.f != undefined && $route.current.params.t != undefined ) {
      $rootScope.globals.view = 'custom';
      var date = moment.utc($route.current.params.f, "YYYY-MM-DD");
      var start = moment.utc($route.current.params.f, "YYYY-MM-DD").format('X');
      var end = moment.utc($route.current.params.t, "YYYY-MM-DD").format('X');

      $rootScope.globals.date = date;
      $rootScope.globals.start = start;
      $rootScope.globals.end = end;
    }
    // Current month by default
    else {
      $scope.currentMonth(false);
    }

    $scope.isActive = function (viewLocation) {
      return $location.path().substring(1, viewLocation.length+1) == viewLocation;
    };

    $scope.updateCustomDates = function(date) {
      $location.search('m', null);

      var startDate = date.startDate;
      var endDate = date.endDate;
      var date = moment.utc(startDate, "YYYY-MM-DD");

      $rootScope.globals.view = 'custom';
      $rootScope.globals.date = date;
      $rootScope.globals.start = startDate.format('X');
      $rootScope.globals.end = endDate.format('X');

      $location.search('f', startDate.format('YYYY-MM-DD'));
      $location.search('t', endDate.format('YYYY-MM-DD'));
    }

    // Default is the current month
    $scope.date = {
        startDate: moment().subtract(1, "days"),
        endDate: moment()
    };
    $scope.dateOps = {
        maxDate: moment().endOf("day"),
        drops: "down",
        autoApply: true,
        showWeekNumbers: true,
        locale: {
            "format": "YYYY-MM-DD",
            "separator": " to ",
            "firstDay": 1
        },
        alwaysShowCalendars: true
    };

  });
