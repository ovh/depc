'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.variables
 * @description
 * # variables
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('variablesService', function ($http, config) {

    var getTeamVariables = function(team_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/variables',
        method: "GET"
      });
    };

    var createTeamVariable = function(team_id, name, type, value) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/variables',
        method: "POST",
        data: {
          "name": name,
          "type": type,
          "value": value
        }
      });
    };

    var createRuleVariable = function(team_id, rule_id, name, type, value) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/rules/' + rule_id + '/variables',
        method: "POST",
        data: {
          "name": name,
          "type": type,
          "value": value
        }
      });
    };

    var createSourceVariable = function(team_id, source_id, name, type, value) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id + '/variables',
        method: "POST",
        data: {
          "name": name,
          "type": type,
          "value": value
        }
      });
    };

    var createCheckVariable = function(team_id, source_id, check_id, name, type, value) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id + '/checks/' + check_id + '/variables',
        method: "POST",
        data: {
          "name": name,
          "type": type,
          "value": value
        }
      });
    };

    var editTeamVariable = function(team_id, variable_id, name, type, value) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/variables/' + variable_id,
        method: "PUT",
        data: {
          "name": name,
          "type": type,
          "value": value
        }
      });
    };

    var editRuleVariable = function(team_id, rule_id, variable_id, name, type, value) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/rules/' + rule_id + '/variables/' + variable_id,
        method: "PUT",
        data: {
          "name": name,
          "type": type,
          "value": value
        }
      });
    };

    var editSourceVariable = function(team_id, source_id, variable_id, name, type, value) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id + '/variables/' + variable_id,
        method: "PUT",
        data: {
          "name": name,
          "type": type,
          "value": value
        }
      });
    };

    var editCheckVariable = function(team_id, source_id, check_id, variable_id, name, type, value) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id + '/checks/' + check_id + '/variables/' + variable_id,
        method: "PUT",
        data: {
          "name": name,
          "type": type,
          "value": value
        }
      });
    };

    var getRuleVariables = function(team_id, rule_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/rules/' + rule_id + '/variables',
        method: "GET"
      });
    };

    var getSourceVariables = function(team_id, source_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id + '/variables',
        method: "GET"
      });
    };

    var getCheckVariables = function(team_id, source_id, check_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id + '/checks/' + check_id + '/variables',
        method: "GET"
      });
    };

    var deleteTeamVariable = function(team_id, variable_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/variables/' + variable_id,
        method: "DELETE"
      });
    };

    var deleteRuleVariable = function(team_id, rule_id, variable_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/rules/' + rule_id + '/variables/' + variable_id,
        method: "DELETE"
      });
    };

    var deleteSourceVariable = function(team_id, source_id, variable_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id + '/variables/' + variable_id,
        method: "DELETE"
      });
    };

    var deleteCheckVariable = function(team_id, source_id, check_id, variable_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/sources/' + source_id + '/checks/' + check_id + '/variables/' + variable_id,
        method: "DELETE"
      });
    };

    return {
      getTeamVariables: getTeamVariables,
      createTeamVariable: createTeamVariable,
      createRuleVariable: createRuleVariable,
      createSourceVariable: createSourceVariable,
      createCheckVariable: createCheckVariable,
      editTeamVariable: editTeamVariable,
      editRuleVariable: editRuleVariable,
      editSourceVariable: editSourceVariable,
      editCheckVariable: editCheckVariable,
      getRuleVariables: getRuleVariables,
      getSourceVariables: getSourceVariables,
      getCheckVariables: getCheckVariables,
      deleteTeamVariable: deleteTeamVariable,
      deleteRuleVariable: deleteRuleVariable,
      deleteSourceVariable: deleteSourceVariable,
      deleteCheckVariable: deleteCheckVariable
	};

  });
