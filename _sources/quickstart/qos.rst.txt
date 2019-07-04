.. _qos:

Step 2 : Compute your QOS
=========================

The **Apache** and **Filer** nodes represent some servers in real life. In
this case we can analyse data in TimeSeries databases, populated by some
probes. Let's see how to do that !

Create the Source
-----------------

DepC can analyse datapoints from a TimeSeries database to compute a QOS.
The first step is to declare a **Source** : it’s basically an URL and a
token used to communicate with the Timeseries database.

DepC only supports **OpenTSDB** and **Warp10** databases for now, but
others will be included in the tool.

But in this quickstart we’ll use a third type of database : the **Fake** one.
We created it for the purpose of this tutorial. This source generates
data on the fly, so you can test DepC without having real probes sending
datapoints into a TimeSeries database.

Go to the Source tab of your team and create a source named
*Tutorial* using the *Fake* plugin :

.. figure:: ../_static/images/quickstart/new_fake_source.png
   :alt: Fake Source

.. note::
   Please note you don't have to add extra parameters, like url or tokens, but
   it will be the case for other kind of sources.

Create The Indicators
---------------------

An indicator is a Python function that queries a source, retrieves the
datapoints and uses it to compute a QoS percentage. Please read the
:ref:`dedicated guide <indicators>` for more information about the indicators.

Thanks to the *Fake* source we have 2 probes which create the following metrics :

-  **depc.tutorial.ping** : the probe launches a ping every 300 seconds
   and returns the response time (in milliseconds).
-  **depc.tutorial.oco** : the probe checks the OCO status every 300
   seconds.

.. note::
   The OCO probe is an internal probe which returns 200 if everything is OK,
   and 300 if the service is down.

Here are the corresponding indicators :

+-------------+-----------+----------------------------------------------+
| Name        | Type      | Parameters                                   |
+=============+===========+==============================================+
| Server Ping | Threshold | Metric: depc.tutorial.ping / Threshold : 20  |
+-------------+-----------+----------------------------------------------+
| Server OCO  | Threshold | Metric: depc.tutorial.oco / Threshold : 299  |
+-------------+-----------+----------------------------------------------+

The indicators can be created in the **Indicators** tab. For example this is the
creation form of the **Server Ping** indicator :

.. figure:: ../_static/images/quickstart/check_server_ping.png
   :alt: Server Ping

Create The Rule
---------------

A rule is simply a group of indicators (an indicator can be added in
multiple rules). We are going to create the **Servers** rule which will
contain our **Server Ping** and **Server OCO** indicators :

1. go to the *Rules* tab, click on the *Create a new rule* button and
   create the **Servers** rule.
2. click on the *Associate an indicator* button, select the wanted indicator
   and click on the *Apply* button.

.. figure:: ../_static/images/quickstart/attach_servers_checks.png
   :alt: Rule Filers Result

The rule is now ready and can be launched. In the *Run* tab, fill the
name with **filer1** and click on the **Launch Checks** button to
execute the rule and its indicators. You can display the details of the
indicators by clicking on the blue button under the *Actions* column :

.. figure:: ../_static/images/quickstart/rule_launched_summary.png
   :alt: Rule Filers Result

Click on the **Display details** button get more information about your
indicator :

.. figure:: ../_static/images/quickstart/rule_details_server_ping.png
   :alt: Indicator Server Ping Details

We can see that some datapoints **exceed our threshold**, so the QOS for
Server Ping is **99.792%**. Likewise the QOS for Server OCO is
**97.708%**.

.. note::
   Please note the whole QOS is **97.5%** because we use a ``AND``
   operation between the indicators of the rule. More information
   about the operations in the :ref:`dedicated guide <queries>`.
