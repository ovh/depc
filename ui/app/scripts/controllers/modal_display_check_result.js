'use strict';

/**
 * @ngdoc function
 * @name depcwebuiApp.controller:ModalDisplayCheckResultCtrl
 * @description
 * # ModalDisplayCheckResultCtrl
 * Controller of the depcwebuiApp
 */
angular.module('depcwebuiApp')
  .controller('ModalDisplayCheckResultCtrl', function ($uibModalInstance, config, result) {
    var unitize = function(value, unit) {
        if (unit !== undefined && unit.length > 0) {
            return value + ' ' + unit;
        }
        else {
            return value;
        }
    };

    var processCheck = function(check) {
        // Create the highcharts data
        var chart = {
            chartType: 'stock',
            chart: {
                zoomType: 'x'
            },
            rangeSelector: {
                enabled: false
            },
            plotOptions: {
                series: {
                    showInNavigator: true,
                    events: {
                        legendItemClick: function (event) {
                            var currentSerie = this;
                            var clickEvent = event.browserEvent;
                            var exclusiveSelect = (clickEvent.ctrlKey  ||
                                                   clickEvent.metaKey  ||
                                                   clickEvent.shiftKey ||
                                                   clickEvent.altKey);
                            if ( exclusiveSelect ) {
                                if ( currentSerie.visible ) {
                                    var wasOneVisible = false;
                                    this.chart.series.forEach(function(serie) {
                                        if (serie !==  currentSerie && serie.visible ) {
                                            serie.hide();
                                            wasOneVisible = true;
                                        }
                                    });
                                    if ( ! wasOneVisible ) {
                                        this.chart.series.forEach(function(serie) {
                                            serie.show();
                                        });
                                    }
                                } else {
                                    this.chart.series.forEach(function(serie) {
                                        ( serie ===  currentSerie ) ? serie.show() : serie.hide();
                                    });
                                }
                            } else {
                                ( currentSerie.visible ) ? currentSerie.hide() : currentSerie.show();
                            }
                            return false;
                        }
                    }
                }
            },
            legend: {
                enabled: true,
                title: {
                    text: '<span>(click to hide a metric, ctrl+click to isolate one)</span>',
                    style: {
                        fontStyle: 'italic',
                        fontSize: '9px',
                        color: '#777'
                    }
                }
            },
            xAxis: {
                ordinal: false
            },
            yAxis: {
                labels: {
                    formatter: function () {
                        return unitize(this.value, check.parameters.unit);
                    }
                },
                plotLines: []
            },
            series: []
        };

        if ( check.type === 'Threshold' ) {
            chart['yAxis']['plotLines'] = [{
                label: {
                    text: 'Critical (' + check.parameters.threshold + ')'
                },
                color: 'red',
                width: 1,
                zIndex: 9,
                dashStyle: 'longdashdot',
                value: check.parameters.threshold
            }];
        }

        if(check.type === 'Interval') {
            chart['yAxis']['plotLines'] = [{
                label: {
                    text: 'Critical (' + check.parameters.top_threshold + ')'
                },
                color: 'red',
                width: 1,
                zIndex: 9,
                dashStyle: 'longdashdot',
                value: check.parameters.top_threshold
            }, {
                label: {
                      text: 'Critical (' + check.parameters.bottom_threshold + ')'
                },
                color: 'red',
                width: 1,
                zIndex: 9,
                dashStyle: 'longdashdot',
                value: check.parameters.bottom_threshold
            }];
        }

        // Transform timeseries to be Highchart compatible
        for ( var i in check.timeseries )
        {
            var data = [];
            for ( var idp in check.timeseries[i].dps ) {
                var dp = check.timeseries[i].dps[idp];
                data.push([parseInt(idp + '000'), dp]);
            }

            var metric = check.timeseries[i].metric;
            var tags = JSON.stringify(check.timeseries[i].tags);

            chart['series'].push({
                name: metric + tags,
                data: data,
                tooltip: {
                    valueDecimals: 3,
                    valueSuffix: check.parameters.unit
                },
                dataGrouping: {
                    enabled: false
                }
            });
        }
        check['chart'] = chart;

        return check;
    };
    this.check = processCheck(result);

    this.getStateByQos = function(qos) {
        return config.getStateByQos(qos);
    };

  });
