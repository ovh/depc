'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalEditRuleCtrl
 * @description
 * # ModalEditRuleCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalEditRuleCtrl', function ($uibModalInstance, teamsService, toastr, team, rule) {
    var self = this;

    // Init variables
    self.team = team;
    self.rule = rule;
    self.name = rule.name;
    self.description = rule.description;

    this.cancel = function () {
      $uibModalInstance.dismiss('cancel');
    };

    this.edit = function() {
        if ( self.name ) {
            teamsService.editTeamRule(self.team.id, self.rule.id, self.name, self.description).then(function(response) {
                toastr.success('Rule ' + self.name + ' has been edited.');
                $uibModalInstance.close(response.data);
            });
        }
    };
  });