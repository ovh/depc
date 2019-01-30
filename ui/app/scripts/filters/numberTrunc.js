'use strict';


/**
 * @ngdoc filter
 * @name depcwebuiApp.filter:numberTrunc
 * @function
 * @description
 * # numberTrunc
 * Filter in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .filter('numberTrunc', function () {
    return function (num, precision) {

      if ( num == undefined || num == null || isNaN(num) ) {
      	return null;
      }
      // javascript's floating point math function are hazardous
      // so we manipulate the string representation instead.
      // see: https://stackoverflow.com/a/11818658/956660
      var re = new RegExp('^-?\\d+(?:\.\\d{0,' + (precision || -1) + '})?');
      return num.toString().match(re)[0];
    };
  }
);
