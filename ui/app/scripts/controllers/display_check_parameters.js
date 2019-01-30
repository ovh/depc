'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalDisplayCheckParametersCtrl
 * @description
 * # ModalDisplayCheckParametersCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalDisplayCheckParametersCtrl', function ($uibModalInstance, check) {
    var self = this;
    self.check = check;
  });