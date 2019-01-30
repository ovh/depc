'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalNewConfigCtrl
 * @description
 * # ModalNewConfigCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalNewConfigCtrl', function ($uibModalInstance, $confirm, toastr, configurationsService, team, placeholder) {
    var self = this;

    // Init variables
    self.team = team;
    self.cmOption = {
      lineNumbers: false,
      theme: 'twilight',
      mode: 'javascript'
    };

    // We prefill the configuration with the placeholder
    self.config = JSON.stringify(placeholder, null, ' ');

    self.cancel = function () {
      $uibModalInstance.dismiss('cancel');
    };


    self.save = function() {
		$confirm({
            text: 'This configuration will remove the previous one (if exists). Are you sure ?',
            title: 'Save the configuration',
            ok: 'Yes',
            cancel: 'No'
        })
        .then(function() {
            try {
                var config = JSON.parse(self.config);
            } catch (e) {
                toastr.error('Your configuration is not valid (must be a JSON object).');
                return false;
            }
            configurationsService.createTeamConfiguration(self.team.id, config).then(function(response) {
                toastr.success('The configuration has been saved.');
                $uibModalInstance.close(response.data);
            });
        });
    };
  });
