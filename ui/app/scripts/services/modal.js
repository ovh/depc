'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.modal
 * @description
 * # modal
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('modalService', function ($uibModal) {

   var changeFromToDate = function(from, to) {
    return $uibModal.open({
        size: 'md',
        templateUrl: 'views/modals/change_from_to_date.html',
        controller: 'ModalChangeFromToDateCtrl',
        controllerAs: 'modalChangeFromToDateCtrl',
        resolve: {
          from: function () {
            return from;
          },
          to: function() {
            return to;
          }
        }
    });
   };

   var displayFullLogs = function(name, service, from, to) {
    return $uibModal.open({
        size: 'lg',
        templateUrl: 'views/modals/display_full_logs.html',
        controller: 'ModalDisplayFullLogsCtrl',
        controllerAs: 'modalDisplayFullLogsCtrl',
        resolve: {
          name: function () {
            return name;
          },
          service: function() {
            return service;
          },
          from: function () {
            return from;
          },
          to: function() {
            return to;
          }
        }
    });
   };

   var displayCheckResult = function(result, qos) {
    return $uibModal.open({
        size: 'xl',
        templateUrl: 'views/modals/display_check_result.html',
        controller: 'ModalDisplayCheckResultCtrl',
        controllerAs: 'modalDisplayCheckResultCtrl',
        resolve: {
          result: function () {
            return result;
          },
          qos: function () {
            return qos;
          }
        }
    });
   };

   var displayGrants = function(team) {
    return $uibModal.open({
        size: 'md',
        templateUrl: 'views/modals/display_grants.html',
        controller: 'ModalDisplayGrantsCtrl',
        controllerAs: 'modalDisplayGrantsCtrl',
        resolve: {
          team: function() {
            return team;
          }
        }
    });
   };

   var newRuleForm = function(team) {
    return $uibModal.open({
        size: 'md',
        templateUrl: 'views/modals/new_rule.html',
        controller: 'ModalNewRuleCtrl',
        controllerAs: 'modalNewRuleCtrl',
        resolve: {
          team: function() {
            return team;
          }
        }
    });
   };

   var editRuleForm = function(team, rule) {
    return $uibModal.open({
        size: 'md',
        templateUrl: 'views/modals/edit_rule.html',
        controller: 'ModalEditRuleCtrl',
        controllerAs: 'modalEditRuleCtrl',
        resolve: {
          team: function() {
            return team;
          },
          rule: function() {
            return rule;
          }
        }
    });
   };

   var associateChecks = function(team, rule) {
    return $uibModal.open({
        size: 'lg',
        templateUrl: 'views/modals/associate_checks.html',
        controller: 'ModalAssociateChecksCtrl',
        controllerAs: 'modalAssociateChecksCtrl',
        resolve: {
          team: function() {
            return team;
          },
          rule: function() {
            return rule;
          }
        }
    });
   };

   var displayCheckParameters = function(check) {
    return $uibModal.open({
        size: 'md',
        templateUrl: 'views/modals/display_check_parameters.html',
        controller: 'ModalDisplayCheckParametersCtrl',
        controllerAs: 'modalDisplayCheckParametersCtrl',
        resolve: {
          check: function() {
            return check;
          }
        }
    });
   };

   var displayConfig = function(team, config) {
    return $uibModal.open({
        size: 'lg',
        templateUrl: 'views/modals/display_config.html',
        controller: 'ModalDisplayConfigCtrl',
        controllerAs: 'modalDisplayConfigCtrl',
        resolve: {
          team: function() {
            return team;
          },
          config: function() {
            return config;
          }
        }
    });
   };

   var newConfig = function(team, placeholder) {
    return $uibModal.open({
        size: 'lg',
        templateUrl: 'views/modals/new_config.html',
        controller: 'ModalNewConfigCtrl',
        controllerAs: 'modalNewConfigCtrl',
        resolve: {
          team: function() {
            return team;
          },
          placeholder: function() {
            return placeholder;
          }
        }
    });
   };

   return {
      changeFromToDate: changeFromToDate,
      displayFullLogs: displayFullLogs,
      displayCheckResult: displayCheckResult,
      displayGrants: displayGrants,
      newRuleForm: newRuleForm,
      editRuleForm: editRuleForm,
      associateChecks: associateChecks,
      displayCheckParameters: displayCheckParameters,
      displayConfig: displayConfig,
      newConfig: newConfig
   };

  });
