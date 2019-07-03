'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.checks
 * @description
 * # checks
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('checksService', function ($http, config) {

    var getTeamChecks = function(team_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/checks',
        method: "GET"
      });
    };

    return {
      getTeamChecks: getTeamChecks
    };
});
