'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.news
 * @description
 * # news
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('newsService', function ($http, config) {

    var getUnreadNews = function() {
      return $http({
        url: config.depc_endpoint() + '/news?unread=1',
        method: "GET"
      });
    };

    var getAllNews = function() {
      return $http({
        url: config.depc_endpoint() + '/news',
        method: "GET"
      });
    };

    var clear = function() {
      return $http({
        url: config.depc_endpoint() + '/news',
        method: "DELETE"
      });
    };

    return {
      getUnreadNews: getUnreadNews,
      getAllNews: getAllNews,
      clear: clear
    };
  });
