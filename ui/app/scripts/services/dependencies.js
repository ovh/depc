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

    var getTeamLabelNode = function(team_id, label, node) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/labels/' + label + '/nodes/' + node + '?alone=1',
        method: "GET"
      });
    };

    var countNodeDependencies = function(team_id, label, node) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/labels/' + label + '/nodes/' + node + '/count',
        method: "GET"
      });
    };

    var getNodeDependencies = function(team_id, label, node, day, filteredByConfig, includingInactive, displayImpacted) {
      var url = config.depc_endpoint() + '/teams/' + team_id + '/labels/' + label + '/nodes/' + node + '?1=1';

      if ( day ) {
        url = url + '&day=' + day;
      }

      if ( filteredByConfig ) {
        url = url + '&config=1';
      }

      if ( includingInactive ) {
        url = url + '&inactive=1';
      }

      if ( displayImpacted ) {
        url = url + '&impacted=1';
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

    var getTeamImpactedNodes = function(teamId, label, node, impactedLabel, skip, limit, unixTs) {
      var url = config.depc_endpoint() + '/teams/' + teamId + '/labels/' + label + '/nodes/' + node + '/impacted';

      // We do not know the order of parameters, so this dirty patch abstracts it
      url += '?1=1';

      if (impactedLabel) {
        url += '&impactedLabel=' + impactedLabel;
      }

      if (skip || skip === 0) {
        url += '&skip=' + skip;
      }

      if (limit || limit === 0) {
        url += '&limit=' + limit;
      }

      if (unixTs || unixTs === 0) {
        url += '&ts=' + unixTs;
      }

      return $http({
        url: url,
        method: "GET"
      });
    };

    var getTeamImpactedNodesCount = function(teamId, label, node, impactedLabel) {
      var url = config.depc_endpoint() + '/teams/' + teamId + '/labels/' + label + '/nodes/' + node + '/impacted/count';

      if (impactedLabel) {
        url += '?impactedLabel=' + impactedLabel;
      }

      return $http({
        url: url,
        method: "GET"
      });
    };

    var getTeamImpactedNodesAll = function(teamId, label, node, impactedLabel, unixTs, inactive) {
      var url = config.depc_endpoint() + '/teams/' + teamId + '/labels/' + label + '/nodes/' + node + '/impacted/all';

      // We do not know the order of parameters, so this dirty patch abstracts it
      url += '?1=1';

      if (impactedLabel) {
        url += '&impactedLabel=' + impactedLabel;
      }

      if (unixTs || unixTs === 0) {
        url += '&ts=' + unixTs;
      }

      if (inactive) {
        url += '&inactive=1';
      }

      return $http({
        url: url,
        method: "GET"
      });
    };

    return {
      getTeamLabels: getTeamLabels,
      getTeamLabelNodes: getTeamLabelNodes,
      getTeamLabelNode: getTeamLabelNode,
      getTeamImpactedNodes: getTeamImpactedNodes,
      getTeamImpactedNodesAll: getTeamImpactedNodesAll,
      getTeamImpactedNodesCount: getTeamImpactedNodesCount,
      countNodeDependencies: countNodeDependencies,
      getNodeDependencies: getNodeDependencies,
      deleteNode: deleteNode
    };
  });
