'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalNewsCtrl
 * @description
 * # ModalNewsCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalNewsCtrl', function ($rootScope, newsService) {
    var self = this;

    self.title = "Latest news";
    self.news = $rootScope.globals.news;

    self.displayAllNews = function() {
        self.title = "All news";
        newsService.getAllNews().then(function(response) {
            self.news = response.data.news;
        });
    };
  });
