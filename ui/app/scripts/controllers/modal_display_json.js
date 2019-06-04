'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalDisplayJsonCtrl
 * @description
 * # ModalDisplayJsonCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalDisplayJsonCtrl', function (title, description, json) {
    var self = this;

    self.title = title;
    self.description = description;
    self.json = JSON.stringify(json, null, ' ');

    self.cmOption = {
        lineNumbers: false,
        theme: 'twilight',
        mode: 'javascript',
        readOnly: true
    };
  });
