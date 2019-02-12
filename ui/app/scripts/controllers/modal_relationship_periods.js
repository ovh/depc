'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalRelationshipPeriodsCtrl
 * @description
 * # ModalRelationshipPeriodsCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalRelationshipPeriodsCtrl', function ($filter, periods) {
    var self = this;

    // Transform the array into list of dict
    var groupedPeriods = [];
    var pushed = false;

    for ( var i in periods ) {
        if ( i % 2 == 0 ) {
            var bar = {'from': periods[i]};
            pushed = false;
        } else {
            bar['to'] = periods[i]
            groupedPeriods.push(bar);
            pushed = true;
        }
    }

    // Last state can be 'from'
    if ( !pushed ) {
        groupedPeriods.push(bar);
    }
    self.periods = groupedPeriods;

    self.getNodeDate = function(d) {
        if (!d) {
          return '--'
        }
        return $filter('date')(d * 1000, 'yyyy-MM-dd HH:mm:ss')
    }
  });
