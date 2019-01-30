.. _queries:

Queries
=======

DepC provides 3 methods to compute the QOS of a node : using a **rule**,
an **operation** or an **aggregation**.

You have to indicate your methods for each labels in your **configuration**.
The following example is directly taken from the :ref:`quickstart <quickstart>` :

.. code:: json

   {
    "Apache": {
     "qos": "rule.Servers"   <-- rule-based QOS
    },
    "Filer": {
     "qos": "rule.Servers"   <-- rule-based QOS
    },
    "Offer": {
     "qos": "aggregation.AVERAGE[Website]"   <-- aggregation-based QOS
    },
    "Website": {
     "qos": "operation.AND[Filer, Apache]"   <-- operation-based QOS
    }
   }

It’s important to understand the difference between these different
methods.

Rule-based QOS
--------------

This QoS is based on datapoints available in a TimeSeries database :
your nodes are monitored with some probes (CPU, RAM, HTTP Status Code...),
and DepC analyses the result.

For example, you have some servers with these 3 probes :

-  probeX : retrieve the CPU load of the server,
-  probeY : retrieve the RAM usage of the server,
-  probeZ : ping the server.

These probes send their results in a TimeSeries database. You can create
a rule containing 3 checks, each of the check querying a probe. The
:ref:`step 3 <qos>` of the tutorial explains how to do that.

You can use the following syntaxes in your configuration :

.. code:: json

   rule.MyRule
   rule.'My rule'

.. note::
    A rule is composed of 1 or multiple checks, usually a team uses one
    check for one probe. Each check returns its own QoS (the method is
    explained :ref:`here <checks>`.

    DepC uses a AND operation between every checks.

Operation-based QOS
-------------------

Sometimes you can not use a rule-based QoS because there is no datapoint to
analyse. In this case DepC can compute the QoS of a node using its parents
QoS.

For example a **Cluster** is a virtual node, its QOS must be
computed from its **servers** :

.. mermaid::
    :align: center

    graph TD;
        C{Cluster A};
        C --> D[Server 1];
        C --> E[Server 2];
        C --> F[Server 3]:

Here the servers could have a rule-based QoS, and you can use an operation QoS for
the cluster.

We provide 4 types of operations :

-  **AND** : the cluster is OK if every servers are OK.
-  **OR** : the cluster is OK if only 1 server is OK.
-  **RATIO** : the cluster is OK if N% of the servers is OK.
-  **ATLEAST** : the cluster is OK if N servers are OK.

**Example**

Consider you choose an AND operation : during the same time (or at the
same timestamp if you prefer), the servers 1 and 2 were OK, but a
problem occurred on the server3. The QOS of the ClusterA will be
impacted. DepC repeats this using a lot of timestamps, so the QOS of the
cluster can be computed.

You can use the following syntaxes in your configuration :

.. code:: json

   operation.AND()[Foo, Bar]
   operation.OR[Foo, Bar]
   operation.OR()[Foo, Bar]
   operation.AND()[Foo]
   operation.AND[Foo]
   operation.AND[A, B, C]
   operation.OR()[A]
   operation.OR[A]
   operation.OR()[A, B]
   operation.RATIO(0.35)[Foo]
   operation.RATIO(0.35)[Foo, Bar]
   operation.ATLEAST(10)[Foo]
   operation.ATLEAST(10)[Foo, Bar]

Aggregation-based QOS
---------------------

Sometimes you don’t want to compare the states of different nodes
because it’s not adapted. It can be useful when you have a lot’s of nodes.

For example imagine an **Offer** nodes containing 100 000 websites. It’s not useful
to use an AND operation (“if one customer is not ok, so the offer is not
ok”). Instead, we would rather compute the average QOS using an **aggregation method** :

-  **AVERAGE** : computes the average QoS,
-  **MIN** : returns the minimum QoS,
-  **MAX** : returns the maximum QoS.

You can use the following syntaxes in your configuration :

.. code:: json

   aggregation.AVERAGE[Foo, Bar]
   aggregation.MAX()[Foo]
   aggregation.MIN()[Foo, Bar]
   aggregation.MIN[Foo, Bar]

.. note::
    **It’s important to note that an aggregation QoS can
    not be followed by an operation QoS.**

    Internally a rule or operation based QoS transform *values* datapoints
    into booleans datapoints (a list of *timestamp:value* becomes a list of *timestamp:boolean*).
    An aggregation QoS simply computes multiple floats into a single float, so we lose the list
    of *timestamp:boolean* DPS.
