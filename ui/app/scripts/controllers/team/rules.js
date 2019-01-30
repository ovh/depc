'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:RulesCtrl
 * @description
 * # RulesCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('RulesCtrl', function ($scope, $interval, $timeout, $rootScope, OvhTailLogs, chartsService, rulesService, teamsService, variablesService, modalService, config, $location, $routeParams, toastr, $confirm) {
    var self = this;

    self.teamName = $routeParams.team;
    self.team = null;
    self.rules = [];
    self.loadingRule = true;
    self.selectedRule = null;
    self.checksResult = {};
    self.ruleExecuting = false;
    this.name = null;
    this.interval = null;
    this.result = null;
    this.checksOrder = 'name';
    self.rulePromise = null;

    self.loadingVariables = false;
    self.variables = [];
    self.logs = [];

    // Dates range
    self.date = {
        startDate: moment().startOf("day"),
        endDate: moment().endOf("day")
    };
    self.dateOps = {
        maxDate: moment().endOf("day"),
        drops: "up",
        autoApply: true,
        showWeekNumbers: true,
        locale: {
            "format": "YYYY-MM-DD",
            "separator": " to ",
            "firstDay": 1
        },
        ranges: {
           'Today': [moment().startOf("day"), moment().endOf("day")],
           'Yesterday': [moment().subtract(1, 'days').startOf("day"), moment().subtract(1, 'days').endOf('day')],
           'Current Week': [moment().startOf('isoWeeks').startOf("day"), moment().endOf("day")],
           'Current Month': [moment().startOf('months').startOf("day"), moment().endOf("day")],
           'Last 2 Days': [moment().subtract(2, 'days').startOf("day"), moment().endOf("day")],
           'Last 7 Days': [moment().subtract(7, 'days').startOf("day"), moment().endOf("day")],
           'Last 30 Days': [moment().subtract(30, 'days').startOf("day"), moment().endOf("day")]
        },
        alwaysShowCalendars: true
    };

    // ChartJS
    this.chartLabels = ['Ok', 'Warning', 'Critical', 'Unknown'];
    this.chartData = [];
    this.chartColors = ["#5cb85c","#f0ad4e","#d9534f", "#808080"];
    this.chartOptions = {
        scales: {
            yAxes: [{
                ticks: {
                    fixedStepSize: 1
                }
            }],
        }
    };

    self.logsExpanded = false;
    self.logsFilterStr = '';
    self.logsDebugEnabled = false;
    self.logsEnableDebug = function() {
        self.logsDebugEnabled = !self.logsDebugEnabled;
    }
    self.logsFilterDebug = function(log) {
        if ( !self.logsDebugEnabled && log.message.level == 'DEBUG') {
            return false;
        }

        return true;
    };

    // We disable this feature for now
    self.fillLogsFilter = function(value) {
        self.logsFilterStr = value;
    };

    self.getPeriodFormat = function(secs, fmt) {
        function getCustomFormat(s) {
            if ( fmt == 'long' ) {
              if (secs >= 86400) { return 'D [day(s)], H [hours], mm [minutes] [and] ss [seconds]'; }
              else if (secs >= 3600) { return 'H [hours], mm [minutes] [and] ss [seconds]'; }
              else if (secs >= 60) { return 'mm [minutes] [and] ss [seconds]'; }
              return 'ss [seconds]';
            } else {
                if (secs >= 86400) { return 'D [day(s)] HH:mm:ss'; }
                else if (secs >= 3600) { return 'HH:mm:ss'; }
                else if (secs >= 60) { return '[00:]mm:ss'; }
                return '[00:00:]ss';
            }
        }
        return moment.utc(secs*1000).format(getCustomFormat(secs))
    };

    teamsService.getTeamByName(self.teamName).then(function(response) {
        self.loadingRule = true;
        self.team = response.data;

        rulesService.getTeamRules(self.team.id).then(function(response) {
            self.rules = response.data.rules;
            self.fillView();
            self.loadingRule = false;
            if ($routeParams.exec === '1') {
              self.executeRule(self.selectedRule);
            }
        });

    });

    this.loadVariables = function() {
        self.loadingVariables = true;
        variablesService.getRuleVariables(self.team.id, self.selectedRule.id).then(function(response) {
            self.variables = response.data;
            self.loadingVariables = false;
        });
    };

    // fill UI based on parameters
    this.fillView = function() {
      if ($routeParams.name) {
        this.name = $routeParams.name;
      }

      self.date = {
        startDate: moment().startOf("day"),
        endDate: moment().endOf("day")
      };

      if ($routeParams.start) {
        self.date.startDate = moment.unix($routeParams.start);
      }

      if ($routeParams.end) {
        self.date.endDate = moment.unix($routeParams.end);
      }

      if ($routeParams.rule) {
        for (var i = 0; i < self.rules.length; i++) {
          if (self.rules[i].name === $routeParams.rule) {
            self.selectRule(self.rules[i]);
          }
        }
      }
    };

    this.selectRule = function(rule) {
        self.resetRule();
        self.selectedRule = rule;
        self.loadVariables();
    };

    this.resetRule = function() {
        self.result = null;
        self.selectedRule = null;
        self.logs = [];
        self.checksResult = {};

        // Reinit query parameters
        $location.search('name', null);
        $location.search('label', null);
        $location.search('start', null);
        $location.search('end', null);
        $location.search('exec', null);
    };

    this.executeRule = function(rule) {
        self.result = null;
        self.checksResult = {};
        self.ruleExecuting = true;
        self.logs = [];

        var start = moment(self.date.startDate).unix();
        var end = moment(self.date.endDate).unix();

        // Change the query parameters
        $location.search('rule', self.selectedRule.name);
        $location.search('name', self.name);
        $location.search('start', start);
        $location.search('end', end);
        $location.search('exec', 1);

        var rule = rulesService.executeRule(self.team.id, self.selectedRule.id, self.name, start, end).then(function(response) {
            var result = response.data.result;

            // Don't wait if cache exists
            self.checkResult(result);

            self.rulePromise = $interval(function() {
                self.checkResult(result);
            }, 1000);

            // Cancel any pending timer
            $scope.$on("$destroy", function () {
                $interval.cancel(self.rulePromise);
            });
        });
    };

    this.hasResult = function() {
        return self.selectedRule && !self.ruleExecuting && self.result;
    }

    this.checkResult = function(result) {
        rulesService.getResult(result, 'asc', 1000).then(function(response) {
            var result = response.data.qos;

            var logs = response.data.logs;
            var tmpLogs = self.logs;
            tmpLogs.push(logs);

            self.logs = _.uniq(_.flatten(tmpLogs), function (log) {
                return log.message._id;
            });

            // Stop the loop, we have our QOS
            if ( result && result.qos ) {
                var stats = {'ok': 0, 'warning': 0, 'critical': 0, 'unknown': 0}

                // Handle each check
                for ( var i in result.checks ) {
                    var check = result.checks[i];

                    // Statistics (Ok, Warning, Critical, Unknown)
                    if ( check.qos == null ) {
                        stats['unknown'] += 1;
                    } else {
                        stats[config.getStateByQos(check.qos)] += 1;
                    }

                    // Add the chart for each check
                    if ( check.timeseries != undefined && check.timeseries.length > 0 ) {
                        var chartData = [];
                        var ts = check.timeseries[0];
                        for ( var dp in  ts.dps) {
                            var val = Number(ts.dps[dp].toFixed(3));
                            chartData.push([dp * 1000, val]);
                        }

                        var metric = ts.metric;
                        var tags = JSON.stringify(ts.tags);

                        // Group the false periods
                        var keys = Object.keys(check.bools_dps);
                        var bands = [];
                        for (var j = 0; j < keys.length-1; j++) {
                          var val = check.bools_dps[keys[j]];
                          if (!val) {
                            bands.push({
                              color: '#ff7272',
                              from: keys[j] * 1000,
                              to: keys[j+1] * 1000
                            });
                          }
                        }

                        var lineChart = chartsService.getCheckChart(115, metric + tags, chartData, bands);
                        result.checks[i]['chart'] = lineChart;
                    }
                }

                // All checks are done
                self.chartData = [stats['ok'], stats['warning'], stats['critical'], stats['unknown']];
                self.result = result;
                $interval.cancel(self.rulePromise);
                self.ruleExecuting = false;
            }
        });
    };

    this.getCheckResult = function(check) {
        if ( check.id in self.checksResult) {
            return self.checksResult[check.id];
        }

        return null;
    };

    this.getCheckDuration = function(check) {
        var result = self.getCheckResult(check);

        if ( result != null ) {
            var duration = Number((parseFloat(result.duration)).toFixed(3));
            return duration + 's';
        }

        return null;
    }

    this.isCheckFinished = function(check) {
        return check.id in self.checksResult;
    }

    this.hasDetails = function(check) {
        return self.isCheckFinished(check) && check.weight != -1;
    };

    this.getCheckProgress = function(check) {
        var check_id = check.id;

        if ( !(check_id in self.checksResult) ) {
            return false;
        } else {
            var result = self.checksResult[check_id];

            // The weight is used to order the list by QOS
            var filteredChecks = self.selectedRule.checks.filter(function(check) {
              return check.id == check_id;
            });
            filteredChecks[0]['weight'] = ( result['qos'] != null ) ? parseFloat(result['qos']) : -1;

            if ( result['qos'] == null ) {
                result['type'] = 'unknown';
            } else {
                result['type'] = config.getStateByQos(result['qos'])
            }

            return result;
        }
    };

    self.getPanel = function(key) {
        var panel = config.getPanelByLevel('unknown');

        // No result means no panel
        if ( self.result != null ) {

            var qos = self.result.qos;

            if ( qos == 'unknown' ) {
                return panel[key];
            }

            if ( key == 'text' ) {
                return qos + '%';
            }

            if ( qos >= 98 ) {
                panel = config.getPanelByLevel('ok');
            } else if ( qos >= 95) {
                panel = config.getPanelByLevel('warning');
            } else {
                panel = config.getPanelByLevel('critical');
            }
        }

        return panel[key];
    };

    this.displayCheckResult = function(check) {
        var c = Object.assign({}, check);
        modalService.displayCheckResult(c);
    };

    this.openNewRuleModal = function() {
        var modalInstance = modalService.newRuleForm(self.team);
        modalInstance.result.then(function(rule) {
            self.rules.push(rule);
        });
    };

    this.openEditRuleModal = function() {
        var modalInstance = modalService.editRuleForm(self.team, self.selectedRule);
        modalInstance.result.then(function(rule) {
            var index = self.rules.indexOf(self.selectedRule);
            if (index > -1) {
                self.rules.splice(index, 1);
            }
            self.rules.push(rule);
            self.selectedRule = rule;
        });
    };

    this.deleteRule = function() {
        $confirm({
            text: 'Are you sure you want to delete the rule "' + self.selectedRule.name + '"?',
            title: 'Delete rule',
            ok: 'Delete',
            cancel: 'Back'
        })
        .then(function() {
            teamsService.deleteTeamRule(self.team.id, self.selectedRule.id).then(function(data) {
                var index = self.rules.indexOf(self.selectedRule);
                if (index > -1) {
                    self.rules.splice(index, 1);
                }
                toastr.success('The rule ' + self.selectedRule.name + ' has been removed.');
                self.resetRule();
            });
        });
    };

    this.openAssociateChecksModal = function() {
        var modalInstance = modalService.associateChecks(self.team, self.selectedRule);
        modalInstance.result.then(function(data) {
            self.selectedRule.checks = data.checks;
        });
    };

    this.openManageGrantsModal = function() {
        modalService.manageGrants(self.team);
    };

    this.openCheckParametersModal = function(check) {
        modalService.displayCheckParameters(check);
    };

    this.openCheckResultModal = function(check) {
        modalService.manageGrants(self.team);
    };

    this.changeOrder = function() {
        if ( self.checksOrder == 'name' ) {
            self.checksOrder = 'weight';
        } else {
            self.checksOrder = 'name';
        }
    }

    this.getLabelClassByQos = function(qos) {
        return config.getLabelClassByQos(qos);
    }

    self.getSlideBg = function(qos) {
        var bg = null;
        if ( parseFloat(qos) < config.getThresholds('error') ) {
            bg = 'bg-error';
        } else if ( parseFloat(qos) < config.getThresholds('warning') ) {
            bg = 'bg-warning';
        } else {
            bg = 'bg-success';
        }
        return bg;
    };

  });
