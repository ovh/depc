'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalAssociateChecksCtrl
 * @description
 * # ModalAssociateChecksCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalAssociateChecksCtrl', function ($uibModalInstance, teamsService, sourcesService, rulesService, toastr, team, rule) {
    var self = this;

    // Init variables
    self.team = team;
    self.rule = rule;
    self.sources = [];
    self.activatedChecks = [];
    self.loader = true;

    sourcesService.getTeamSources(self.team.id).then(function(response) {
      self.sources = response.data.sources;

      for ( var check in self.rule.checks ) {
        self.activatedChecks.push(self.rule.checks[check].id);
      }
      self.loader = false;
    });

    this.addCheck = function(check) {
      var idx = self.activatedChecks.indexOf(check.id);

      if (idx > -1) {
        self.activatedChecks.splice(idx, 1);
      } else {
        self.activatedChecks.push(check.id);
      }
    };

    this.apply = function() {
        if ( self.activatedChecks ) {
            rulesService.associateRuleChecks(self.team.id, self.rule.id, self.activatedChecks).then(function(response) {
                toastr.success('Checks have been updated.');
                $uibModalInstance.close(response.data);
            });
        }
    };

    this.cancel = function () {
      $uibModalInstance.dismiss('cancel');
    };

  });