'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.users
 * @description
 * # users
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('usersService', function ($http, config) {

    var getCurrentUser = function() {
      return $http({
        url: config.depc_endpoint() + '/users/me',
        method: "GET"
      });
    };

    var getUsers = function() {
      return $http({
        url: config.depc_endpoint() + '/users',
        method: "GET"
      });
    };

    return {
      getCurrentUser: getCurrentUser,
      getUsers: getUsers
    };
  });