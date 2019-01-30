'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalDisplayConfigCtrl
 * @description
 * # ModalDisplayConfigCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalDisplayConfigCtrl', function ($uibModalInstance, $confirm, toastr, configurationsService, team, config) {
    var self = this;

    // Init variables
    self.team = team;
    self.config = config;
    self.jsonConfig = JSON.stringify(self.config.data, null, ' ');
    self.cmOption = {
      lineNumbers: false,
      theme: 'twilight',
      mode: 'javascript',
      readOnly: true
    };

    this.cancel = function () {
      $uibModalInstance.dismiss('cancel');
    };

    this.revert = function() {
        $confirm({
            text: 'Are you sure you want to revert the "' + self.config.created_at + '" version ?',
            title: 'Revert the configuration',
            ok: 'Yes',
            cancel: 'No'
        })
        .then(function() {
            configurationsService.revertTeamConfiguration(self.team.id, self.config.id).then(function(response) {
                toastr.success('The configuration has been reverted.');
                $uibModalInstance.close(response.data);
            });
        });
    };
  });