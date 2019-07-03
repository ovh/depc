DepC Documentation
==================

.. toctree::
   :hidden:
   :maxdepth: 2

   Overview <self>

   installation
   quickstart/index
   guides/index
   api/index

DepC (Dependency Checker) is a project used to **compute the QOS** of
your whole infrastucture, based on **TimeSeries and Graph** databases.

.. warning::
   Please note DepC is under active development and is still in **Beta**.

Overview
--------

The tool allows you to compute the QOS for every node of your
infrastructure. The main steps to do this are :

1. Pushing your nodes and their relationships into a Graph Database.
2. Giving us the method to compute the QOS of your nodes.

.. figure:: _static/images/qos_dependencies.png
   :alt: Dependencies QOS

Dependencies
~~~~~~~~~~~~

DepC allows you to push your nodes and their relationships into a Graph
Database : we use `Neo4j <https://neo4j.com/>`__ as the Graph database
to manage your nodes and their relationships.

In order to scale, we created a Kafka consumer which listens some topics
: you have just to send your nodes and their relationships using a
:ref:`specific format <kafka>`, and we fully manage the database for you.
We also provide a WebUI for a better user experience.

.. note::
   The nodes and their relationships are **versioned**,
   so we can know exactly what are the dependencies of a node within a
   particular period (which is a crucial need to compute an accurate QOS).

QOS
~~~

A common usage in OVH is to create some probes that check a server
health (for example), and send the result in a TimeSeries database. The
data can be anything like the response time of a server, its RAM and CPU
usage, its number of IO Waits, etc.

Based on this principle, we have created a **Rule** system that queries
the datapoints and computes a QOS from it. For example you can decide
that any datapoints exceeding a given threshold will lower the QOS.
These computing methods are explained in a :ref:`dedicated page <indicators>`.

.. figure:: _static/images/quickstart/rule_details_server_ping.png
   :alt: QOS API

.. note::
   DepC currently supports 2 TimeSeries databases :
   **OpenTSDB** & **Warp10**. Our goal is to add other data sources like
   InfluxDB, Graphite or even Prometheus.

Architecture
------------

.. figure:: _static/images/architecture.png
   :alt: Architecture
   :scale: 50 %
   :align: center
