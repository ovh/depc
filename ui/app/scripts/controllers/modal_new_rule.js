'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalNewRuleCtrl
 * @description
 * # ModalNewRuleCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalNewRuleCtrl', function ($uibModalInstance, teamsService, toastr, team) {
    var self = this;

    // Init variables
    self.name = null;
    self.description = null;
    self.team = team;

    this.cancel = function () {
      $uibModalInstance.dismiss('cancel');
    };

    this.create = function() {
        if ( self.name ) {
            teamsService.createTeamRule(self.team.id, self.name, self.description).then(function(response) {
    			toastr.success('Rule ' + self.name + ' has been created.');
				$uibModalInstance.close(response.data);
			});
    	}
    };
  });