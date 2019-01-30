'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.sources
 * @description
 * # sources
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('sourcesService', function ($http, config) {

    var getAvailableSources = function() {
      return $http({
        url: config.depc_endpoint() + '/sources',
        method: "GET"
      });
    };

    var getAvailableSourceInfo = function(source_name) {
      return $http({
        url: config.depc_endpoint() + '/sources/' + source_name,
        method: "GET"
      });
    };

    var getAvailableChecks = function(source_name) {
      return $http({
        url: config.depc_endpoint() + '/sources/' + source_name + '/checks',
        method: "GET"
      });
    };

    var getAvailableCheckInfo = function(source_name, check_type) {
      return $http({
        url: config.depc_endpoint() + '/sources/' + source_name + '/checks/' + check_type,
        method: "GET"
      });
    };

    var getTeamSources = function(team_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources',
        method: "GET"
      });
    };

    var createTeamSource = function(team_id, name, plugin, configuration) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources',
        method: "POST",
        data: {
          "name": name,
          "plugin": plugin,
          "configuration": configuration
        }
      });
    };

    var editTeamSource = function(team_id, source_id, name, plugin, configuration) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id,
        method: "PUT",
        data: {
          "name": name,
          "plugin": plugin,
          "configuration": configuration
        }
      });
    };

    var deleteTeamSource = function(team_id, source_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id,
        method: "DELETE"
      });
    }

    var createTeamCheck = function(team_id, source_id, name, type, parameters) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id + '/checks',
        method: "POST",
        data: {
          "name": name,
          "type": type,
          "parameters": parameters
        }
      });
    };

    var editTeamCheck = function(team_id, source_id, check_id, name, type, parameters) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id + '/checks/' + check_id,
        method: "PUT",
        data: {
          "name": name,
          "type": type,
          "parameters": parameters
        }
      });
    };

    var deleteTeamCheck = function(team_id, source_id, check_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id + '/checks/' + check_id,
        method: "DELETE"
      });
    };

    return {
      getAvailableSources: getAvailableSources,
      getAvailableSourceInfo: getAvailableSourceInfo,
      getAvailableChecks: getAvailableChecks,
      getAvailableCheckInfo: getAvailableCheckInfo,
      getTeamSources: getTeamSources,
      createTeamSource: createTeamSource,
      editTeamSource: editTeamSource,
      deleteTeamSource: deleteTeamSource,
      createTeamCheck: createTeamCheck,
      editTeamCheck: editTeamCheck,
      deleteTeamCheck: deleteTeamCheck
    };
  });
