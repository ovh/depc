'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ChecksCtrl
 * @description
 * # ChecksCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ChecksCtrl', function ($routeParams, $confirm, toastr, $location, modalService, teamsService, sourcesService, rulesService, checksService) {
    var self = this;

    self.teamName = $routeParams.team;
    self.team = null;
    
    self.availableChecks = ["Threshold", "Interval"];
    self.availableSources = [];

    self.check = null;
    self.checks = [];

    self.filteredTitle = '';
    self.sources = [];

    self.ruleFiltered = null;
    self.rules = [];

    self.mode = null;
    self.name = null;
    self.parameters = {};

    self.sourceOpened = false;
    self.checkOpened = false;
    self.cmOption = {
      lineNumbers: false,
      theme: 'twilight',
      mode: 'javascript',
      readOnly: false
    };

    self.load = function() {
        self.checks = [];
        self.loadingSources = true;
        self.loadingRules = true;

        teamsService.getTeamByName(self.teamName).then(function(response) {
            self.team = response.data;

            sourcesService.getTeamSources(self.team.id).then(function(response) {
                self.sources = response.data.sources;
                var name = $routeParams.source;

                for ( var i in self.sources ) {
                    self.checks.push.apply(self.checks, self.sources[i]["checks"]);

                    if ( name != null && self.sources[i].name == name ) {
                        self.selectSource(self.sources[i]);
                    }
                }

                if ( !name ) {
                    self.filteredTitle = self.checks.length;
                } else {
                    self.filteredTitle = self.sourceFiltered.checks.length  + ' ouf of ' + self.checks.length;
                }
                self.loadingSources = false;
            });
    
            rulesService.getTeamRules(self.team.id).then(function(response) {
                self.rules = response.data.rules;
                self.loadingRules = false;

                for ( var idx_rule in self.rules ) {
                    for ( var idx_check in self.rules[idx_rule]["checks"] ) {
                        //console.log(self.rules[idx_rule]["checks"][idx_check]);
                    }
                }
    
                // Select a specific rule
                var name = $routeParams.rule;
                if ( name != null ) {
                    for ( var i in self.rules ) {

                        if ( self.rules[i].name == name ) {
                            self.selectRule(self.rules[i]);
                        }
                    }
                }
            });

        });
    };
    self.load();

    // Get the list of availables sources to display their information
    sourcesService.getAvailableSources().then(function(response) {
        self.availableSources = response.data.sources;
    });

    self.resetAll = function() {
        self.mode = null;
        self.check = null;
        self.sourceFiltered = null;
        self.ruleFiltered = null;
        self.filteredTitle = self.checks.length;
        $location.search('source', null)
        $location.search('rule', null)
    }

    self.selectRule = function(rule) {
        self.resetAll();
        self.filteredTitle = rule.checks.length  + ' ouf of ' + self.checks.length;
        self.ruleFiltered = rule;
        $location.search('rule', self.ruleFiltered.name);
    }

    self.selectSource = function(source) {
        self.resetAll();
        self.filteredTitle = source.checks.length  + ' ouf of ' + self.checks.length;
        self.sourceFiltered = source;
        $location.search('source', self.sourceFiltered.name);
    };

    self.filteredChecks = function() {
        if ( self.sourceFiltered ) {
            var checks = [];
            for ( var i in self.checks ) {
                if ( self.checks[i]["source_id"] == self.sourceFiltered["id"] ) {
                    checks.push(self.checks[i]);
                }
            }
            return checks;
        } else if ( self.ruleFiltered ) {
            var checks = [];

            var rule_check_ids = [];
            for ( var i in self.ruleFiltered.checks ) {
                rule_check_ids.push(self.ruleFiltered.checks[i]["id"])
            }

            for ( var i in self.checks ) {
                var index = rule_check_ids.indexOf(self.checks[i]["id"]);
                if (index > -1) {
                    checks.push(self.checks[i]);
                }
            }

            return checks;
        } else {
            return self.checks;
        }
    }

    this.newCheck = function() {
        self.resetAll();
        self.mode = 'newCheck';
        self.name = null;
        self.threshold = 0;
        self.query = "";
        self.parameters = {};
    };

    self.editCheck = function(check) {
        self.mode = 'editCheck';
        $location.search('source', null),
        $location.search('rule', null),
        self.check = check;
        self.name = check.name;
        self.parameters = check.parameters;
        self.query = check.parameters.query;
        self.threshold = check.parameters.threshold;
    };

    this.save = function() {
        // Guess the type of check
        var type = "Threshold";
        if (self.threshold.toString().indexOf(':') > -1) {
            type = "Interval";
        }


        // Edit an existing check
        if ( self.mode == 'editCheck' ) {
            var params = {
                'query': self.query,
                'threshold': self.threshold.toString()
            };

            sourcesService.editTeamCheck(self.team.id, self.check.source_id, self.check.id, self.name, type, params).then(function(response) {
                toastr.success('Check ' + self.name + ' has been edited.');
                self.load();
            });
        }

        // Create a new check
        if ( self.mode == 'newCheck' ) {
            var params = {
                'query': self.query,
                'threshold': self.threshold.toString()
            };

            sourcesService.createTeamCheck(self.team.id, self.source.id, self.name, type, params).then(function(response) {
                var data = response.data;
                data["source_id"] = self.source.id;

                // Add the new check in the lists
                self.checks.push(data);
                self.filteredTitle = self.checks.length;
                for ( var i in self.sources ) {
                    if ( self.sources[i].id == self.source.id ) {
                        self.sources[i].checks.push(data);
                    }
                }
                self.editCheck(data);
                toastr.success('Check ' + self.name + ' has been created.');
            });
        }
    };

    this.openNewRuleModal = function() {
        var modalInstance = modalService.newRuleForm(self.team);
        modalInstance.result.then(function(rule) {
            self.rules.push(rule);
            self.selectRule(rule);
        });
    };

    this.openEditRuleModal = function() {
        var modalInstance = modalService.editRuleForm(self.team, self.ruleFiltered);
        modalInstance.result.then(function(rule) {
            var index = self.rules.indexOf(self.ruleFiltered);
            if (index > -1) {
                self.rules.splice(index, 1);
            }
            self.rules.push(rule);
            self.selectRule(rule);
        });
    };

    this.deleteRule = function() {
        $confirm({
            text: 'Are you sure you want to delete the rule "' + self.ruleFiltered.name + '"?',
            title: 'Delete rule',
            ok: 'Delete',
            cancel: 'Back'
        })
        .then(function() {
            teamsService.deleteTeamRule(self.team.id, self.ruleFiltered.id).then(function(data) {
                var index = self.rules.indexOf(self.ruleFiltered);
                if (index > -1) {
                    self.rules.splice(index, 1);
                }
                toastr.success('The rule ' + self.ruleFiltered.name + ' has been removed.');
                self.resetAll();
            });
        });
    };

    this.openNewSourceModal = function() {
        var modalInstance = modalService.newSourceForm(self.team);
        modalInstance.result.then(function(source) {
            self.sources.push(source);
            self.selectSource(source);
        });
    };

    this.openEditSourceModal = function() {
        var modalInstance = modalService.editSourceForm(self.team, self.sourceFiltered);
        modalInstance.result.then(function(source) {
            var index = self.sources.indexOf(self.sourceFiltered);
            if (index > -1) {
                self.sources.splice(index, 1);
            }
            self.sources.push(source);
            self.selectSource(source);
        });
    };

    this.deleteSource = function() {
        $confirm({
            text: 'Are you sure you want to delete the source "' + self.sourceFiltered.name + '"?',
            title: 'Delete source',
            ok: 'Delete',
            cancel: 'Back'
        })
        .then(function() {
            sourcesService.deleteTeamSource(self.team.id, self.sourceFiltered.id).then(function(data) {
                var index = self.sources.indexOf(self.sourceFiltered);
                if (index > -1) {
                    self.sources.splice(index, 1);
                }

                toastr.success('The source ' + self.sourceFiltered.name + ' has been removed.');
                self.resetAll();
            });
        });
    };

    this.openAssociateChecksModal = function() {
        var modalInstance = modalService.associateChecks(self.team, self.ruleFiltered);
        modalInstance.result.then(function(data) {
            self.load();
        });
    };

    this.deleteCheck = function() {
        $confirm({
            text: 'Are you sure you want to delete the check "' + self.check.name + '"?',
            title: 'Delete check',
            ok: 'Delete',
            cancel: 'Back'
        })
        .then(function() {
            sourcesService.deleteTeamCheck(self.team.id, self.check.source_id, self.check.id).then(function(data) {
                toastr.success('The check ' + self.check.name + ' has been removed.');
                self.resetAll();
                self.load();
            });
        });
    };

  });
