'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:VariablesCtrl
 * @description
 * # VariablesCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('VariablesCtrl', function ($scope, $location, $routeParams, $rootScope, $confirm, toastr, teamsService, rulesService, sourcesService, variablesService) {
    var self = this;

    self.teamName = $routeParams.team;
    self.team = null;

    self.loadingVariables = true;
    self.mode = 'new';
    self.variables = [];
    self.availableTypes = ['string', 'text', 'number'];

    self.level = $routeParams.level || 'Team';
    self.levels = ['Team', 'Rule', 'Source', 'Check'];
    self.source = null;
    self.sources = [];
    self.check = null;
    self.checks = [];
    self.rule = null;
    self.rules = [];

    self.variable = null;
    self.name = null;
    self.type = 'string';
    self.value = null;

    var cmLoad = function(_editor) {
        _editor.on("keyup", function() {

            // Check if the given number is valid
            if ( self.type === 'number' ) {
                var reg = /^(?=.)([+-]?([0-9]*)(\.([0-9]+))?)\.?$/;
                if ( ! reg.test(self.value) ) {
                    _editor.setValue('');
                }
            }
        });
    };

    self.cmOption = {
        lineNumbers: false,
        theme: 'twilight',
        mode: 'javascript',
        readOnly: false,
        onLoad : cmLoad
    };

    this.changeCm = function() {
        if ( self.type === 'text' ) {
            self.cmOption['lineNumbers'] = true;
        } else {
            self.cmOption['lineNumbers'] = false;
        }
    };

    this.newVariable = function() {
        self.mode = 'new';
        self.variable = null;
        self.name = null;
        self.type = 'string';
        self.value = null;
    };

    this.editVariable = function(variable) {
        self.mode = 'edit';
        self.name = variable.name;
        self.type = variable.type;
        self.value = null;

        // Cast numbers for the 'number' input
        var value = variable.value;
        if ( self.type === 'number' ) {
            value = Number(value);
        }

        self.value = value;
        self.variable = variable;
    };

    this.save = function() {

        if ( self.name && self.type ) {

            // This field accepts numbers, but database stores it as string
            if ( self.type === 'number' ) {
                if ( isNaN(self.value) ) {
                    self.value = '0';
                } else {
                    self.value = String(self.value);
                }
            }

            // Edit an existing variable
            if ( self.mode === 'edit' ) {
                var query = null;

                // Each level has its own endpoint (team level by default)
                if ( self.level === 'Rule' ) {
                    query = variablesService.editRuleVariable(self.team.id, self.rule.id, self.variable.id, self.name, self.type, self.value);
                } else if ( self.level === 'Source' ) {
                    query = variablesService.editSourceVariable(self.team.id, self.source.id, self.variable.id, self.name, self.type, self.value);
                } else if ( self.level === 'Check' ) {
                    query = variablesService.editCheckVariable(self.team.id, self.source.id, self.check.id, self.variable.id, self.name, self.type, self.value);
                } else {
                    // Team level by default
                    query = variablesService.editTeamVariable(self.team.id, self.variable.id, self.name, self.type, self.value);
                }

                query.then(function(response) {
                    var data = response.data;
                    var index = self.variables.indexOf(self.variable);
                    if (index > -1) {
                        self.variables.splice(index, 1);
                    }
                    self.variables.push(data);
                    toastr.success('Variable ' + self.name + ' has been edited.');
                    self.editVariable(data);
                });
            }

            // Create a new variable
            if ( self.mode === 'new' ) {
                var query = null;

                // Each level has its own endpoint
                if ( self.level === 'Rule' ) {
                    query = variablesService.createRuleVariable(self.team.id, self.rule.id, self.name, self.type, self.value);
                } else if ( self.level === 'Source' ) {
                    query = variablesService.createSourceVariable(self.team.id, self.source.id, self.name, self.type, self.value);
                } else if ( self.level === 'Check' ) {
                    query = variablesService.createCheckVariable(self.team.id, self.source.id, self.check.id, self.name, self.type, self.value);
                } else {
                    // Team level by default
                    query = variablesService.createTeamVariable(self.team.id, self.name, self.type, self.value);
                }

                // Notify the user
                query.then(function(response) {
                    var data = response.data;
                    self.variables.push(data);
                    toastr.success('Variable ' + self.name + ' has been created.');
                    self.editVariable(data);
                });
            }
        }
    };

    this.deleteVariable = function() {
        $confirm({
            text: 'Are you sure you want to delete the variable "' + self.variable.name + '"?',
            title: 'Delete variable',
            ok: 'Delete',
            cancel: 'Back'
        })
        .then(function() {
            var query = null;

            // Each level has its own endpoint (team level by default)
            if ( self.level === 'Rule' ) {
                query = variablesService.deleteRuleVariable(self.team.id, self.rule.id, self.variable.id);
            } else if ( self.level === 'Source' ) {
                query = variablesService.deleteSourceVariable(self.team.id, self.source.id, self.variable.id);
            } else if ( self.level === 'Check' ) {
                query = variablesService.deleteCheckVariable(self.team.id, self.source.id, self.check.id, self.variable.id);
            } else {
                // Team level by default
                query = variablesService.deleteTeamVariable(self.team.id, self.variable.id);
            }

            query.then(function(data) {
                var index = self.variables.indexOf(self.variable);
                if (index > -1) {
                    self.variables.splice(index, 1);
                }

                toastr.success('The variable ' + self.variable.name + ' has been removed.');
                self.newVariable();
            });
        });
    };

    this.selectLevel = function() {
        self.loadingVariables = true;
        self.variables = [];
        self.newVariable();

        $rootScope.$watch('checkGrants', function () {
            teamsService.getTeamByName(self.teamName).then(function(response) {
                self.team = response.data;

                if ( $rootScope.checkGrants(self.teamName, ['user']) ) {

                    // Team variables
                    if ( self.level === 'Team' ) {
                        variablesService.getTeamVariables(self.team.id).then(function(response) {
                            self.variables = response.data;
                            self.loadingVariables = false;
                        });
                    }

                    // Rule variables
                    if ( self.level === 'Rule' ) {
                        rulesService.getTeamRules(self.team.id).then(function(response) {
                            self.rules = response.data.rules;

                            var rule = $routeParams.rule;
                            if ( rule != null ) {
                                for ( var i in self.rules ) {
                                    if ( self.rules[i].name == rule ) {
                                        self.selectRule(self.rules[i]);
                                    }
                                }
                            } else if ( self.rules.length > 0 ) {
                                self.selectRule(self.rules[0]);
                            }
                        });
                    }

                    // Source variables
                    if ( self.level === 'Source' || self.level === 'Check') {
                        sourcesService.getTeamSources(self.team.id).then(function(response) {
                            self.sources = response.data.sources;

                            var source = $routeParams.source;
                            if ( source != null ) {
                                for ( var i in self.sources ) {
                                    if ( self.sources[i].name == source ) {
                                        self.selectSource(self.sources[i]);
                                    }
                                }
                            } else if ( self.sources.length > 0 ) {
                                self.selectSource(self.sources[0]);
                            }
                        });
                    }

                    // Check variables
                    if ( self.level === 'Check' ) {
                        self.loadingVariables = false;
                    }

                } else {
                    self.loadingVariables = false;
                }
            });
        });
    };

    this.selectRule = function(rule) {
        self.loadingVariables = true;
        self.variables = [];
        self.newVariable();
        self.rule = rule;

        variablesService.getRuleVariables(self.team.id, self.rule.id).then(function(response) {
            self.variables = response.data;
            self.loadingVariables = false;
        });
    };

    this.selectSource = function(source) {
        self.loadingVariables = true;
        self.variables = [];
        self.newVariable();

        self.source = source;
        self.checks = source.checks;

        if ( self.level === 'Source' ) {
            variablesService.getSourceVariables(self.team.id, self.source.id).then(function(response) {
                self.variables = response.data;
                self.loadingVariables = false;
            });
        }

        if ( self.level === 'Check' ) {
            var check = $routeParams.check;
            if ( check != null ) {
                for ( var i in self.checks ) {
                    if ( self.checks[i].name == check ) {
                        self.selectCheck(self.checks[i]);
                    }
                }
            } else if ( self.checks.length > 0 ) {
                self.selectCheck(self.checks[0]);
            }
        }
    };

    this.selectCheck = function(check) {
        self.loadingVariables = true;
        self.variables = [];
        self.newVariable();
        self.check = check;

        variablesService.getCheckVariables(self.team.id, self.source.id, self.check.id).then(function(response) {
            self.variables = response.data;
            self.loadingVariables = false;
        });
    };

    self.selectLevel();

  });
