'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalNewSourceCtrl
 * @description
 * # ModalNewSourceCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalNewSourceCtrl', function ($uibModalInstance, sourcesService, toastr, team) {
    var self = this;

    // Init variables
    self.team = team;
    self.name = null;
    self.plugin = null;
    self.configuration = {};
  
    sourcesService.getAvailableSources().then(function(response) {
      self.availablePlugins = response.data.sources;
    });

    this.cancel = function () {
      $uibModalInstance.dismiss('cancel');
    };

    this.create = function() {
      sourcesService.createTeamSource(self.team.id, self.name, self.plugin.name, self.configuration).then(function(response) {
        toastr.success('Source ' + self.name + ' has been created.');
        $uibModalInstance.close(response.data);
      });
    };
  });