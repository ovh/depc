'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:TeamsCtrl
 * @description
 * # TeamsCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('TeamsCtrl', function (teamsService, usersService, config, modalService) {
  	var self = this;

  	self.teams = [];
    self.teamsLoading = true;
    teamsService.getTeams().then(function(response) {
      var teams = response.data.teams;

      // Be sure user.grants exists before using it
      usersService.getCurrentUser().then(function(response) {
        var grants = response.data.grants;

        // Group team (memberOf or not)
        var data = {
          'userOf': {
            'title': 'Your teams',
            'teams': []
          },
          'notUserOf': {
            'title': 'Other teams',
            'teams': []
          }
        };
        for ( var i in teams ) {
          if ( teams[i].name in grants ) {
            data.userOf.teams.push(teams[i]);
          } else {
            data.notUserOf.teams.push(teams[i]);
          }
        }

        self.teams = data;
        self.teamsLoading = false;
      });
    });

    this.displayGrants = function(team) {
        modalService.displayGrants(team);
    };

    this.countTotalChecks = function(team) {
        var count = 0;
        for ( var rule in team.rules ) {
          count += team.rules[rule].checks.length;
        }
        return config.pluralize(count, 'check', 'checks', true);
    };

    this.displayManagers = function(team) {
      teamsService.getTeamGrants(team.id).then(function(response) {
        var grants = [];

        // Keep the managers
        for ( var i in response.data ) {
          if ( response.data[i].role == "manager" ) {
            grants.push(response.data[i].user);
          }
        }

        modalService.displayJson(
          "List of managers",
          "<div class='alert alert-info'>Contact one of this people if you want to join the team.</div>",
          grants
        );
      });
    };

  });
