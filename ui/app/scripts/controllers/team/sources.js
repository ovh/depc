'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:SourcesCtrl
 * @description
 * # SourcesCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('SourcesCtrl', function ($routeParams, $rootScope, $confirm, toastr, teamsService, sourcesService, variablesService) {
  	var self = this;

    self.teamName = $routeParams.team;
    self.team = null;
    self.sources = [];
    self.source = null;
    self.loadingSource = true;

    self.loadingVariables = false;
    self.variables = [];

    self.mode = 'new';
    self.name = null;
    self.plugin = null;
    self.configuration = {};

    self.opened = false;

    $rootScope.$watch('checkGrants', function () {
        teamsService.getTeamByName(self.teamName).then(function(response) {
            self.team = response.data;

            if ( $rootScope.checkGrants(self.teamName, ['user']) ) {
                sourcesService.getTeamSources(self.team.id).then(function(response) {
                    self.sources= response.data.sources;
                    self.loadingSource = false;
                });
            }
        });
    });

    sourcesService.getAvailableSources().then(function(response) {
      self.availablePlugins = response.data.sources;
    });

    this.loadVariables = function() {
        self.loadingVariables = true;
        variablesService.getSourceVariables(self.team.id, self.source.id).then(function(response) {
            self.variables = response.data;
            self.loadingVariables = false;
        });
    };

    this.newSource = function() {
        self.source = null;
        self.mode = 'new';
        self.name = null;
        self.plugin = null;
        self.configuration = {};
    };

    this.editSource = function(source) {
        self.mode = 'edit';
    	self.source = source;
        self.name = source.name;

        // Load the variables
        self.loadVariables();

        // Find the corresponding plugin
        for ( var i in self.availablePlugins ) {
            if ( self.availablePlugins[i].name == source.plugin ) {
                self.plugin = self.availablePlugins[i];
            }
        };
        self.configuration = source.configuration;
    };

    this.selectPlugin = function(plugin) {
        self.plugin = plugin;
    };

    this.save = function() {
        if ( self.name && self.plugin && self.configuration ) {

            // Edit an existing source
            if ( self.mode == 'edit' ) {
                sourcesService.editTeamSource(self.team.id, self.source.id, self.name, self.plugin.name, self.configuration).then(function(response) {
                    var data = response.data;
                    var index = self.sources.indexOf(self.source);
                    if (index > -1) {
                        self.sources.splice(index, 1);
                    }
                    self.sources.push(data);
                    self.source = data;
                    toastr.success('Source ' + self.name + ' has been edited.');
                });
            }

            // Create a new source
            if ( self.mode == 'new' ) {
                sourcesService.createTeamSource(self.team.id, self.name, self.plugin.name, self.configuration).then(function(response) {
                    var data = response.data;
                    self.sources.push(data);
                    self.editSource(data);
                    toastr.success('Source ' + self.name + ' has been created.');
                });
            }
        }
    };

    this.deleteSource = function() {
        $confirm({
            text: 'Are you sure you want to delete the source "' + self.source.name + '"?',
            title: 'Delete source',
            ok: 'Delete',
            cancel: 'Back'
        })
        .then(function() {
            sourcesService.deleteTeamSource(self.team.id, self.source.id).then(function(data) {
                var index = self.sources.indexOf(self.source);
                if (index > -1) {
                    self.sources.splice(index, 1);
                }

                toastr.success('The source ' + self.source.name + ' has been removed.');
                self.newSource();
            });
        });
    };

  });
