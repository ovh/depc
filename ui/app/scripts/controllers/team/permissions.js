'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:PermissionsCtrl
 * @description
 * # PermissionsCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('PermissionsCtrl', function ($routeParams, $rootScope, toastr, teamsService, usersService) {
    var self = this;

    self.teamName = $routeParams.team;
    self.search = '';
    self.load = true;

    this.refresh = function() {
        self.load = true;
        self.users = [];
        self.grants = [];

        usersService.getUsers().then(function(response) {
            self.users = response.data.users;
        });

        teamsService.getTeamByName(self.teamName).then(function(response) {
            self.team = response.data;

            teamsService.getTeamGrants(self.team.id).then(function(response) {
                var grants = response.data;
                for ( var grant in grants ) {
                    self.grants[grants[grant]['user']] = grants[grant]['role'];
                };

                self.load = false;
            });
        });
    };

    // Load the data
    self.refresh();

    this.applyGrants = function() {
        self.load = true;

        var grants = [];
        for ( var grant in self.grants ) {
            grants.push({
                'user': grant,
                'role': self.grants[grant]
            });
        };

        teamsService.associateTeamGrants(self.team.id, grants).then(function(response) {
            if ( response.status == 200 ) {
                self.refresh();
                toastr.success('Grants have been updated.');
            }
        });

    };

    this.fillSearch = function(username) {
        self.search = username;
    }
});