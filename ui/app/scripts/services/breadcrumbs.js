'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.breadcrumbs
 * @description
 * # breadcrumbs
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('breadcrumbs', function ($rootScope, $location, $route) {

  	var breadcrumbs = [],
        breadcrumbsService = {},
        routes = $route.routes;

    var generateBreadcrumbs = function() {
        breadcrumbs = [];
        var pathElements = $location.path().split('/'),
            path = '';

        var getRoute = function(route) {
            angular.forEach($route.current.params, function(value, key) {
                var re = new RegExp(value);
                route = route.replace(re, ':' + key);
            });
            return route;
        };
        if (pathElements[1] == '') delete pathElements[1];
        angular.forEach(pathElements, function(el) {
            path += path === '/' ? el : '/' + el;
            var route = getRoute(path);

            // The following url uses the wildcard to handle names
            // containing a "/", we need to transform it.
            if (route == '/teams/:team/dashboard/:label/:name') {
                route = '/teams/:team/dashboard/:label/:name*'
            }

            if (routes[route] && routes[route].label) {
            	var label = routes[route].label;
            	if ( label.startsWith(':') ) {
            		label = label.substring(1)
            		label = $route.current.params[label]
            	}
                breadcrumbs.push({ label: label, path: path });
            }
        });
    };

    // We want to update breadcrumbs only when a route is actually changed
    // as $location.path() will get updated immediately (even if route change fails!)
    $rootScope.$on('$routeChangeSuccess', function(event, current) {
        generateBreadcrumbs();
    });

    breadcrumbsService.getAll = function() {
        return breadcrumbs;
    };

    breadcrumbsService.getFirst = function() {
        return breadcrumbs[0] || {};
    };

	return breadcrumbsService;
  });
