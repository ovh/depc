'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.dependencies
 * @description
 * # dependencies
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('dependenciesService', function ($http, config) {

    var getTeamLabels = function(team_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/labels',
        method: "GET"
      });
    };

    var getTeamLabelNodes = function(team_id, label, name, limit, random) {
      var url = config.depc_endpoint() + '/teams/' + team_id + '/labels/' + label + '/nodes';

      // We do not know the order of parameters, so this dirty patch abstracts it
      url += '?1=1'

      if ( name != null ) {
        url = url + '&name=' + name;
      }

      if ( limit != null ) {
        url = url + '&limit=' + limit;
      }

      if ( random != null ) {
        url = url + '&random=1';
      }

      return $http({
        url: url,
        method: "GET"
      });
    };

    var countNodeDependencies = function(team_id, label, node) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/labels/' + label + '/nodes/' + node + '/count',
        method: "GET"
      });
    };

    var getNodeDependencies = function(team_id, label, node, day, filteredByConfig, includingOldNodes) {
      var url = config.depc_endpoint() + '/teams/' + team_id + '/labels/' + label + '/nodes/' + node + '?1=1';

      if ( day ) {
        url = url + '&day=' + day;
      }

      if ( filteredByConfig ) {
        url = url + '&with_config=1';
      }

      if ( includingOldNodes ) {
        url = url + '&with_olds=1';
      }

      return $http({
        url: url,
        method: "GET"
      });
    };

    var deleteNode = function(team_id, label, node, detach) {
      var url = config.depc_endpoint() + '/teams/' + team_id + '/labels/' + label + '/nodes/' + node;

      if ( detach ) {
        url = url + '?detach=1';
      }

      return $http({
        url: url,
        method: "DELETE"
      });
    }

    return {
      getTeamLabels: getTeamLabels,
      getTeamLabelNodes: getTeamLabelNodes,
      countNodeDependencies: countNodeDependencies,
      getNodeDependencies: getNodeDependencies,
      deleteNode: deleteNode
    };
  });
