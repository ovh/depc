'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.configurations
 * @description
 * # configurations
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('configurationsService', function ($http, config) {

    var getTeamConfigurations = function(team_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/configs',
        method: "GET"
      });
    };

    var getTeamCurrentConfiguration = function(team_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/configs/current',
        method: "GET"
      });
    };

    var revertTeamConfiguration = function(team_id, config_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/configs/' + config_id + '/apply',
        method: "PUT",
        data: {}
      });
    };

    var createTeamConfiguration = function(team_id, conf) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/configs',
        method: "POST",
        data: conf
      });
    };

    return {
      getTeamConfigurations: getTeamConfigurations,
      getTeamCurrentConfiguration: getTeamCurrentConfiguration,
      revertTeamConfiguration: revertTeamConfiguration,
      createTeamConfiguration: createTeamConfiguration
    }
  });