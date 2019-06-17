'use strict';

/**
 * @ngdoc overview
 * @name depcwebuiApp
 * @description
 * # depcwebuiApp
 *
 * Main module of the application.
 */
angular
  .module('depcwebuiApp', [
    'ngAnimate',
    'ngCookies',
    'ngResource',
    'ngRoute',
    'ngSanitize',
    'ngTouch',
    'angular.filter',
    'schemaForm',
    'ui.bootstrap',
    'ui.codemirror',
    'ui.bootstrap.datetimepicker',
    'ngVis',
    'highcharts-ng',
    'toastr',
    'angular-confirm',
    'chart.js',
    'daterangepicker',
  ])
  .config(function ($routeProvider, $locationProvider, $httpProvider, schemaFormProvider) {
    $routeProvider
      .when('/', {
        redirectTo: '/teams'
      })
      .when('/teams', {
        templateUrl: 'views/teams.html',
        controller: 'TeamsCtrl',
        controllerAs: 'teamsCtrl',
        reloadOnSearch: false,
        label: 'Teams'
      })
      .when('/teams/:team', {
       redirectTo: '/teams/:team/dashboard',
       label: ':team'
      })
      .when('/teams/:team/dashboard', {
        templateUrl: 'views/team/dashboard.html',
        controller: 'DashboardCtrl',
        controllerAs: 'dashboardCtrl',
        reloadOnSearch: false,
        label: 'Dashboard'
      })
      .when('/teams/:team/dependencies', {
        templateUrl: 'views/team/dependencies.html',
        controller: 'DependenciesCtrl',
        controllerAs: 'dependenciesCtrl',
        reloadOnSearch: false,
        label: 'Dependencies'
      })
      .when('/teams/:team/dashboard/:label', {
        templateUrl: 'views/team/label.html',
        controller: 'LabelCtrl',
        controllerAs: 'labelCtrl',
        reloadOnSearch: false,
        label: ':label'
      })
      .when('/teams/:team/dashboard/:label/:name*', {
        templateUrl: 'views/team/item.html',
        controller: 'ItemCtrl',
        controllerAs: 'itemCtrl',
        reloadOnSearch: false,
        label: ':name'
      })
      .when('/teams/:team/rules', {
        templateUrl: 'views/team/rules.html',
        controller: 'RulesCtrl',
        controllerAs: 'rulesCtrl',
        reloadOnSearch: false,
        label: 'Rules'
      })
      .when('/teams/:team/sources', {
        templateUrl: 'views/team/sources.html',
        controller: 'SourcesCtrl',
        controllerAs: 'sourcesCtrl',
        reloadOnSearch: false,
        label: 'Sources'
      })
      .when('/teams/:team/checks', {
        templateUrl: 'views/team/checks.html',
        controller: 'ChecksCtrl',
        controllerAs: 'checksCtrl',
        reloadOnSearch: false,
        label: 'Checks'
      })
      .when('/teams/:team/variables', {
        templateUrl: 'views/team/variables.html',
        controller: 'VariablesCtrl',
        controllerAs: 'variablesCtrl',
        reloadOnSearch: false,
        label: 'Variables'
      })
      .when('/teams/:team/permissions', {
        templateUrl: 'views/team/permissions.html',
        controller: 'PermissionsCtrl',
        controllerAs: 'permissionsCtrl',
        reloadOnSearch: false,
        label: 'Permissions'
      })
      .when('/teams/:team/configuration', {
        templateUrl: 'views/team/configuration.html',
        controller: 'ConfigurationCtrl',
        controllerAs: 'configurationCtrl',
        reloadOnSearch: false,
        label: 'Configuration'
      })
      .when('/teams/:team/statistics', {
        templateUrl: 'views/team/statistics.html',
        controller: 'StatisticsCtrl',
        controllerAs: 'statisticsCtrl',
        reloadOnSearch: false,
        label: 'Statistics'
      })
      .otherwise({
        redirectTo: '/'
      });

      $locationProvider.html5Mode(false).hashPrefix('');

      $httpProvider.interceptors.push('httpInterceptor');

      // Customize the dynamic fields from JSON
      schemaFormProvider.postProcess(function(form) {
          for ( var i in form ) {
            form[i]['feedback'] = false;
            form[i]['disableSuccessState'] = true;

            // Customize Codemirror fields
            if ( form[i]['type'] == 'codemirror' ) {
              form[i]['feedback'] = true;
              form[i].codemirrorOptions = {
                  lineNumbers: false,
                  mode: "javascript",
                  theme: "twilight",
                  autoRefresh: true,
              }
            }
          }
          return form;
      });

  })
  .run(['$rootScope', '$anchorScroll', '$location', 'toastr', '$confirmModalDefaults', '$route', 'breadcrumbs', 'usersService', 'newsService',
    function ($rootScope, $anchorScroll, $location, toastr, $confirmModalDefaults, $route, breadcrumbs, usersService, newsService) {
      $rootScope.globals = {
        date: moment.utc()
      };
      $rootScope.checkGrants = function() { return false; };

      // Load the current user
      usersService.getCurrentUser().then(function(response) {
        var user = response.data;
        $rootScope.globals['currentUser'] = user;

        // Check the grants of the current users
        $rootScope.checkGrants = function(team, grants) {
          if ( team in user.grants ) {
            if ( grants.indexOf('user') > -1 ) {
              return true;
            }

            if ( grants.indexOf(user.grants[team]) > -1 ) {
              return true;
            }
          }
          return false;
        };
      });

      // Load the latest news for this user
      newsService.getUnreadNews().then(function(response) {
        $rootScope.globals['news'] = response.data.news;
      });

      $rootScope.getDateUrlParams = function() {
        if ( $route.current.params.m != undefined ) {
          return '?m=' + $route.current.params.m;
        }

        if ( $route.current.params.f != undefined && $route.current.params.t != undefined ) {
          return '?f=' + $route.current.params.f + '&t=' + $route.current.params.t;
        }
      };

      // Bind errors to toastr
      $rootScope.$on('requestError', function (event, args) {
        if ( args && args.hasOwnProperty("message") ) {
          toastr.error(args.message);

          // Redirect to homepage
          if ( args.message.includes('You do not have the required permissions') ) {
            $location.path( "/teams" );
          }
        }
      });

      // Set default template for the confirm modal
      $confirmModalDefaults.templateUrl = 'views/modals/confirm.html';

      $rootScope.$on('$locationChangeStart', function () {
        function startsWith( str, compar ) {
          return str.substring( 0, compar.length ) === compar;
        }
      });

      $rootScope.breadcrumbs = breadcrumbs;

      // Offset of 70 because of the header
      $anchorScroll.yOffset = 70;

      // Workaround : auto-refresh for CodeMirror
      // Credits from http://codemirror.net/addon/display/autorefresh.js
      (function(mod) {
        if (typeof exports == "object" && typeof module == "object") // CommonJS
          mod(require("../../lib/codemirror"))
        else if (typeof define == "function" && define.amd) // AMD
          define(["../../lib/codemirror"], mod)
        else // Plain browser env
          mod(CodeMirror)
      })(function(CodeMirror) {
        "use strict"

        CodeMirror.defineOption("autoRefresh", false, function(cm, val) {
          if (cm.state.autoRefresh) {
            stopListening(cm, cm.state.autoRefresh)
            cm.state.autoRefresh = null
          }
          if (val && cm.display.wrapper.offsetHeight == 0)
            startListening(cm, cm.state.autoRefresh = {delay: val.delay || 250})
        })

        function startListening(cm, state) {
          function check() {
            if (cm.display.wrapper.offsetHeight) {
              stopListening(cm, state)
              if (cm.display.lastWrapHeight != cm.display.wrapper.clientHeight)
                cm.refresh()
            } else {
              state.timeout = setTimeout(check, state.delay)
            }
          }
          state.timeout = setTimeout(check, state.delay)
          state.hurry = function() {
            clearTimeout(state.timeout)
            state.timeout = setTimeout(check, 50)
          }
          CodeMirror.on(window, "mouseup", state.hurry)
          CodeMirror.on(window, "keyup", state.hurry)
        }

        function stopListening(_cm, state) {
          clearTimeout(state.timeout)
          CodeMirror.off(window, "mouseup", state.hurry)
          CodeMirror.off(window, "keyup", state.hurry)
        }
      });

    }]
  );
