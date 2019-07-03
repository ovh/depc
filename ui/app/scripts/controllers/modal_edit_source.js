'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalEditSourceCtrl
 * @description
 * # ModalEditSourceCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalEditSourceCtrl', function ($uibModalInstance, sourcesService, toastr, team, source) {
    var self = this;

    // Init variables
    self.team = team;
    self.source = source;
    self.name = source.name;
    self.configuration = source.configuration;

    sourcesService.getAvailableSourceInfo(source.plugin).then(function(response) {
      self.plugin = response.data;
    });

    this.cancel = function () {
      $uibModalInstance.dismiss('cancel');
    };

    this.edit = function() {
      sourcesService.editTeamSource(self.team.id, self.source.id, self.name, self.plugin.name, self.configuration).then(function(response) {
        toastr.success('Source ' + self.name + ' has been edited.');
        $uibModalInstance.close(response.data);
      });
    };
  });