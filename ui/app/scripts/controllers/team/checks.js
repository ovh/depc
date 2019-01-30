'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ChecksCtrl
 * @description
 * # ChecksCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ChecksCtrl', function ($routeParams, $rootScope, $confirm, toastr, $location, config, teamsService, sourcesService, variablesService) {
    var self = this;

    self.teamName = $routeParams.team;
    self.team = null;
    self.source = null;
    self.check = null;
    self.sources = [];
    self.availableChecks = [];
    self.availableSources = [];
    self.sourceDescription = null;
    self.loadingSources = true;

    self.loadingVariables = false;
    self.variables = [];

    self.mode = 'new';
    self.name = null;
    self.type = null;
    self.parameters = {};

    self.sourceOpened = false;
    self.checkOpened = false;
    self.cmOption = {
      lineNumbers: false,
      theme: 'twilight',
      mode: 'javascript',
      readOnly: false
    };

    $rootScope.$watch('checkGrants', function () {
        teamsService.getTeamByName(self.teamName).then(function(response) {
            self.team = response.data;

            if ( $rootScope.checkGrants(self.teamName, ['user']) ) {
                sourcesService.getTeamSources(self.team.id).then(function(response) {
                    self.sources= response.data.sources;
                    self.loadingSources = false;

                    // Select a specific source if URL is specified
                    var name = $routeParams.source;
                    if ( name != null ) {
                        for ( var i in self.sources ) {
                            if ( self.sources[i].name == name ) {
                                self.selectSource(self.sources[i]);
                            }
                        }
                    }
                });
            }
        });
    });

    // Get the list of availables sources to display their information
    sourcesService.getAvailableSources().then(function(response) {
        self.availableSources = response.data.sources;
    });

    self.selectSource = function(source) {
        self.source = source;
        self.newCheck();

        // Set the source in URL
        $location.search('source', self.source.name);

        // Get this source description from the whole sources list
        for ( var i in self.availableSources ) {
            if ( self.availableSources[i].name == self.source.plugin ) {
                self.sourceDescription = self.availableSources[i].description;
            }
        }

        // Get the associated checks
        sourcesService.getAvailableChecks(source.plugin).then(function(response) {
          self.availableChecks = response.data.checks;
        });
    };

    this.loadVariables = function() {
        self.loadingVariables = true;
        variablesService.getCheckVariables(self.team.id, self.source.id, self.check.id).then(function(response) {
            self.variables = response.data;
            self.loadingVariables = false;
        });
    };

    this.newCheck = function() {
        self.check = null;
        self.mode = 'new';
        self.name = null;
        self.type = null;
        self.parameters = {};
    };

    self.editCheck = function(check) {
        self.mode = 'edit';
        self.check = check;
        self.name = check.name;

        // Load the variables
        self.loadVariables();

        // Find the corresponding type
        for ( var i in self.availableChecks ) {
            if ( self.availableChecks[i].name == check.type ) {
                self.type = self.availableChecks[i];
            }
        };

        self.parameters = check.parameters;
    };

    this.isReadyToSubmit = function() {
        return self.name && self.type && self.parameters;
    };

    this.save = function() {
        if ( self.isReadyToSubmit() ) {
            // Edit an existing check
            if ( self.mode == 'edit' ) {
                sourcesService.editTeamCheck(self.team.id, self.source.id, self.check.id, self.name, self.type.name, self.parameters).then(function(response) {
                    var data = response.data;
                    var index = self.source.checks.indexOf(self.check);
                    if (index > -1) {
                        self.source.checks.splice(index, 1);
                    }
                    self.source.checks.push(data);
                    self.check = data;
                    toastr.success('Check ' + self.name + ' has been edited.');
                });
            }

            // Create a new check
            if ( self.mode == 'new' ) {
                sourcesService.createTeamCheck(self.team.id, self.source.id, self.name, self.type.name, self.parameters).then(function(response) {
                    var data = response.data;
                    self.source.checks.push(data);
                    self.editCheck(data);
                    toastr.success('Check ' + self.name + ' has been created.');
                });
            }
        }
    };

    this.deleteCheck = function() {
        $confirm({
            text: 'Are you sure you want to delete the check "' + self.check.name + '"?',
            title: 'Delete check',
            ok: 'Delete',
            cancel: 'Back'
        })
        .then(function() {
            sourcesService.deleteTeamCheck(self.team.id, self.source.id, self.check.id).then(function(data) {
                var index = self.source.checks.indexOf(self.check);
                if (index > -1) {
                    self.source.checks.splice(index, 1);
                }

                toastr.success('The check ' + self.check.name + ' has been removed.');
                self.newCheck();
            });
        });
    };

  });
