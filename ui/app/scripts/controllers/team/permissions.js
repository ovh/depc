'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:PermissionsCtrl
 * @description
 * # PermissionsCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('PermissionsCtrl', function ($routeParams, $scope, toastr, teamsService, usersService) {
    var self = this;

    self.teamName = $routeParams.team;
    self.search = '';
    self.load = true;
    self.includeOther = false;

    this.refresh = function() {
        self.load = true;
        self.users = [];
        self.grants = [];

        teamsService.getTeamByName(self.teamName).then(function(response) {
            self.team = response.data;

            usersService.getUsers().then(function(response) {
                var users = response.data.users;

                teamsService.getTeamGrants(self.team.id).then(function(response) {
                    var grants = response.data;
                    var grantedUsers = [];
                    for ( var grant in grants ) {
                        grantedUsers.push(grants[grant].user);
                        self.grants[grants[grant]['user']] = grants[grant]['role'];
                    };

                    if ( self.includeOther ) {
                        self.users = users;
                    } else {
                        var users_copy = []
                        for ( var user in users ) {
                            if ( grantedUsers.indexOf(users[user].name) > -1 ) {
                                users_copy.push(users[user]);
                            }
                        }
                        self.users = users_copy;
                    }

                    self.load = false;
                });
            });
        });
    };

    // Load the data
    self.refresh();
    $scope.$watch(function() {
        return self.includeOther;
      }, function() {
          self.refresh();
      }, true);

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