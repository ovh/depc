'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.rules
 * @description
 * # rules
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('rulesService', function ($http, config) {

    var getTeamRules = function(team_name) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_name + '/rules',
        method: "GET"
      });
    };

    var getCheck = function(check_id) {
      return $http({
        url: config.depc_endpoint() + '/checks/' + check_id,
        method: "GET"
      });
    };

    var executeRule = function(team_id, rule_or_label, name, start, end) {
      var name = name || "";
      var data = {
        'name': name,
        'start': start,
        'end': end
      };

      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/rules/' + rule_or_label + '/execute',
        method: "POST",
        data: data
      });
    };

    var associateRuleChecks = function(team_id, rule_id, checks) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/rules/' + rule_id + '/checks',
        method: "PUT",
        data: {
          "checks": checks
        }
      });
    };

    var removeRuleLabel = function(team_id, rule_id, label) {
      return $http({
          url: config.depc_endpoint() + '/teams/' + team_id + '/rules/' + rule_id + '/labels/' + label,
          method: "DELETE"
      });
    };

    return {
      getTeamRules: getTeamRules,
      executeRule: executeRule,
      getCheck: getCheck,
      associateRuleChecks: associateRuleChecks,
      removeRuleLabel: removeRuleLabel
    };
  });
