'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.httpInterceptor
 * @description
 * # httpInterceptor
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('httpInterceptor', function ($rootScope, $q) {

    return {
     'responseError': function(rejection) {
        $rootScope.$broadcast('requestError', rejection.data);
        return $q.reject(rejection);
      },
      'request': function(config) {
        // config.headers['X-Remote-User'] = 'username';
        return config;
      }
    };
  });

