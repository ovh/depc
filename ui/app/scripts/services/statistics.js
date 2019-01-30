'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.statistics
 * @description
 * # statistics
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('statisticsService', function ($http, config) {

    var getTeamStatistics = function(team_id, sort, start, end) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/statistics?sort=' + sort + '&start=' + start + '&end=' + end,
        method: "GET"
      });
    };

    return {
      getTeamStatistics: getTeamStatistics
    }
  });