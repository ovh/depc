'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.teams
 * @description
 * # teams
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('teamsService', function ($http, config) {

    var getTeams = function() {
      var url = config.depc_endpoint() + '/teams';

      return $http({
        url: url,
        method: "GET"
      });
    };

    var getTeamByName = function(team_name) {
      return $http({
        url: config.depc_endpoint() + '/teams?name=' + team_name,
        method: "GET"
      });
    };

    var getTeamRules = function(team_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id,
        method: "GET"
      });
    };

    var createTeamRule = function(team_id, name, description) {
      var data = {
        "name": name
      };

      if ( description != null ) {
        data['description'] = description;
      }

      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/rules',
        method: "POST",
        data: data
      });
    };

    var editTeamRule = function(team_id, rule_id, name, description) {
      var data = {};

      if ( name != null ) {
        data['name'] = name;
      }

      if ( description != null ) {
        data['description'] = description;
      }

      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/rules/' + rule_id,
        method: "PUT",
        data: data
      });
    };

    var deleteTeamRule = function(team_id, rule_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/rules/' + rule_id,
        method: "DELETE"
      });
    }

    var getTeamGrants = function(team_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/grants',
        method: "GET"
      });
    };

    var associateTeamGrants = function(team_id, grants) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/grants',
        method: "PUT",
        data: {
          "grants": grants
        }
      });
    };

    var exportGrafana = function(team_id, view) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/export/grafana?view=' + view,
        method: "GET"
      });
    };

    return {
      getTeams: getTeams,
      getTeamByName: getTeamByName,
      getTeamRules: getTeamRules,
      createTeamRule: createTeamRule,
      editTeamRule: editTeamRule,
      deleteTeamRule: deleteTeamRule,
      getTeamGrants: getTeamGrants,
      associateTeamGrants: associateTeamGrants,
      exportGrafana: exportGrafana
    };
  });
