'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.qos
 * @description
 * # qos
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('qosService', function ($http, config) {

    var lookup = function() {
      return $http({
        url: config.depc_endpoint() + '/qos/lookup',
        method: "GET"
      });
    };

    var getInfraQos = function(start, end, label) {
      var url = config.depc_endpoint() + '/qos/infra?start=' + start + '&end=' + end;

      if ( label != null ) {
        url = url + '&label=' + label;
      }

      return $http({
        url: url,
        method: "GET"
      });
    };

    var getClustersQos = function(start, end, cluster) {
      var url = config.depc_endpoint() + '/qos/clusters?start=' + start + '&end=' + end;

      if ( cluster != null ) {
        url = url + '&cluster=' + cluster;
      }

      return $http({
        url: url,
        method: "GET"
      });
    };

    var getCustomersQos = function(start, end) {
      return $http({
        url: config.depc_endpoint() + '/qos/customers?start=' + start + '&end=' + end,
        method: "GET"
      });
    };

    var getCustomerQos = function(start, end, customer) {
      return $http({
        url: config.depc_endpoint() + '/qos/customers/' + customer + '?start=' + start + '&end=' + end,
        method: "GET"
      });
    };

    var getInfraLabelQos = function(start, end, label) {
      return $http({
        url: config.depc_endpoint() + '/qos/infra/' + label + '?start=' + start + '&end=' + end,
        method: "GET"
      });
    };

    var getInfraItemQos = function(start, end, label, name) {
      return $http({
        url: config.depc_endpoint() + '/qos/infra/' + label + '/' + name + '?start=' + start + '&end=' + end,
        method: "GET"
      });
    };

    var getWorstCustomers = function(start, end, cluster, count) {
      var url = config.depc_endpoint() + '/qos/worst/customers?start=' + start + '&end=' + end;

      if ( cluster != null ) {
        url = url + '&cluster=' + cluster;
      }

      if ( count != null ) {
        url = url + '&count=' + count;
      }

      return $http({
        url: url,
        method: "GET"
      });
    };

    var getWorstInfra = function(start, end, label, count) {
      var url = config.depc_endpoint() + '/qos/worst/infra?start=' + start + '&end=' + end;

      if ( label != null ) {
        url = url + '&label=' + label;
      }

      if ( count != null ) {
        url = url + '&count=' + count;
      }

      return $http({
        url: url,
        method: "GET"
      });
    };

    var getTeamQos = function(start, end, team_id) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/qos?start=' + start + '&end=' + end,
        method: "GET"
      });
    };

    var getTeamLabelQos = function(start, end, team_id, label) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/qos?label='+ label + '&start=' + start + '&end=' + end,
        method: "GET"
      });
    };

    var getTeamItemQos = function(start, end, team_id, label, name) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/qos?label='+ label + '&name=' + name + '&start=' + start + '&end=' + end,
        method: "GET"
      });
    };

    var getTeamWorstItemQos = function(team_id, label, date) {
      return $http({
        url: config.depc_endpoint() + '/teams/' + team_id + '/qos/worst?label='+ label + '&date=' + date,
        method: "GET"
      });
    };

    return {
      lookup: lookup,
      getInfraQos: getInfraQos,
      getClustersQos: getClustersQos,
      getCustomersQos: getCustomersQos,
      getCustomerQos: getCustomerQos,
      getInfraLabelQos: getInfraLabelQos,
      getInfraItemQos: getInfraItemQos,
      getWorstCustomers: getWorstCustomers,
      getWorstInfra: getWorstInfra,
      getTeamQos: getTeamQos,
      getTeamLabelQos: getTeamLabelQos,
      getTeamItemQos: getTeamItemQos,
      getTeamWorstItemQos: getTeamWorstItemQos
    };
  });
