'use strict';

/**
 * @ngdoc service
 * @name depcwebuiApp.charts
 * @description
 * # charts
 * Service in the depcwebuiApp.
 */
angular.module('depcwebuiApp')
  .service('chartsService', function ($http, config) {

    var getCheckChart = function(size, name, data, plotbands) {
      return {
        credits: false,
        chart: {
            type: 'line',
            height: size
        },
        legend: {
          enabled: false
        },
        global: {
          useUTC: false
        },
        title: {
          text: null
        },
        xAxis: {
            type: 'datetime',
            startOnTick: false,
            endOnTick: false,
            title: {
              text: null
            },
            minTickInterval: moment.duration(1, 'day').milliseconds(),
            plotBands: plotbands
        },
        yAxis: {
          title: {
            text: null
          }
        },
        plotOptions: {
          series: {
            animation: false
          },
          scatter: {
            tooltip: {
                  headerFormat: '<b>{point.x:%Y-%m-%d}</b><br />',
                  pointFormat: '<span style="color:{point.color}">\u25CF</span> {point.y}%'
              }
          }
        },
        series: [{
            name: name,
            data: data
        }]
      };
    };

    var getChartLine = function(title, xtitle, ytitle, height, showBands, min, max, html, click_fn) {
      var chart = {
        credits: false,
        chart: {
            type: 'line',
            height: height
        },
        legend: {
          enabled: false
        },
        global: {
          useUTC: false
        },
        title: {
          text: title,
          margin: 40
        },
        xAxis: {
            type: 'datetime',
            startOnTick: false,
            endOnTick: false,
            title: {
              text: xtitle
            },
            minTickInterval: moment.duration(1, 'day').milliseconds()
        },
        yAxis: {
          floor: 0,
          ceiling: 100,
          title: {
            text: ytitle
          },
          plotLines: [{
              color: 'red',
              width: 1,
              zIndex: 9,
              dashStyle: 'DashDot',
              value: config.getThresholds('error')
          }, {
              color: 'orange',
              width: 1,
              zIndex: 9,
              dashStyle: 'DashDot',
              value: config.getThresholds('warning')
          }]
        },
        plotOptions: {
          series: {
            animation: false
          },
          scatter: {
            tooltip: {
                  headerFormat: '<b>{point.x:%Y-%m-%d}</b><br />',
                  pointFormat: '<span style="color:{point.color}">\u25CF</span> {point.y}%'
              }
          }
        },
        series: [{
            name: 'QoS',
            data: [],
            zones: [{
                    value: config.getThresholds('error'),
                    color: '#DE451F'
                }, {
                    value: config.getThresholds('warning'),
                    color: '#FFB436'
                },{
                    color: '#39B336'
                }
            ],
            negativeColor: '#39B336',
            threshold: config.getThresholds('warning'),
            color: 'red',
            tooltip: {
                valueDecimals: 3
            }
        }]
      };

      if ( html != null ) {
        chart['tooltip'] = {
            enabled: true,
            useHTML: true,
            pointFormat: html,
            style: {
              pointerEvents: 'auto'
            }
        }
      }

      if ( click_fn != null ) {
        chart['plotOptions']['series']['cursor'] = 'pointer';
        chart['plotOptions']['series']['point'] = {
          events: {
            click: click_fn
          }
        }
      }

      if( showBands !== false ) {
        chart['yAxis']['plotBands'] = [{
              color: '#FCB3B5',
              from: 0,
              to: config.getThresholds('error')
          }, {
              color: '#FCDDA7',
              from: config.getThresholds('error'),
              to: config.getThresholds('warning')
          }, {
              color: '#D8FCD7',
              from: config.getThresholds('warning'),
              to: 110
          }];
      }

      if ( !isNaN(min) ) {
        chart['yAxis']['min'] = min;
      }

      if ( !isNaN(max) ) {
        chart['yAxis']['max'] = max;
      }

      return chart;
    };

    var getSimpleChart = function() {
      var chart = {
        credits: false,
        chart: {
            type: 'line',
            height: null
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
        global: {
          useUTC: true
        },
        title: {
          text: null,
          margin: 40
        },
        xAxis: {
            type: 'datetime',
            startOnTick: false,
            endOnTick: false,
            title: {
              text: null
            },
            minTickInterval: moment.duration(1, 'day').milliseconds()
        },
        yAxis: {
          floor: 0,
          //ceiling: 100,
          title: {
            text: null
          }
        },
        plotOptions: {
          series: {
            animation: false,
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
          },
          scatter: {
            tooltip: {
                  headerFormat: '<b>{point.x:%Y-%m-%d}</b><br />',
                  pointFormat: '<span style="color:{point.color}">\u25CF</span> {point.y}%'
              }
          }
        },
        series: []
      };

      return chart;
    };

    return {
      getChartLine: getChartLine,
      getCheckChart: getCheckChart,
      getSimpleChart: getSimpleChart
    };
  });
