.. _difference-qos-sla:

QoS and SLA
===========

One of the feature provided by DepC is to compute the QoS of your nodes,
whether servers, web services or even customers. So it's important to know
the difference between QoS and SLA, but also what are SLO and SLI.

QoS (Quality of Service)
------------------------

A QoS is a percentage telling you what is (or what was) the state of a specific
service. This state is very subjective but in general it refers to the ability
for a customer to consume its services in good conditions. So we can talk here
about the **availability** of the service.

For example in DepC, a website which is available **from 0:00:00 to 23:59:59**
will have a QoS of **100%**. This QoS can be decreased each time the website is
not reachable. In the extreme case where he would not be reachable for an entire
day, it's QoS will be **0%**.

SLA (Service Level Agreement)
-----------------------------

A SLA is a contract between a provider and its customers, telling it what is
the awaited quality of service. Being a commitment signed by both parties, the
SLA can also contains penalties if the quality is not good.

So it's possible to see mentions about QoS in a SLA, for example "we commit
ourselves to provide an uptime of 99.99% for the product XXX". But keep in mind
that a **QoS is not the same as a SLA**.

SLO (Service Level Objectif)
----------------------------

The SLO refers to the objective that a provider wants to reach in term of QoS.
Let's imagine the QoS of a specific service is 99.95% : the provider may
want to improve this percentage and give a SLO of 99.99%.

SLI (Service Level Indicator)
-----------------------------

The SLI is in the heart of DepC : an indicator is a measurement used to compute
a QoS (and so to reach a SLO). It can be everything that can be measurable over
a period of time :

- an HTTP Status Code,
- the response time of a Ping,
- the RAM usage,
- ... and so on.

DepC uses TimeSeries databases to retrieve raw data. The idea is pretty simple :
let's imagine we need to compute the QoS of an API : we could analyse the HTTP
status code and reject every status which is above 500 (internal server error).

If we analyse a period containing 100 HTTP status code (called datapoints in a
Time Series DB) with 20 status above 500, the QoS will be **80%** (100 - 20).

DepC is able to combine multiple :ref:`indicators <indicators>` to compute a
QoS.
