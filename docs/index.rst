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

DepC (Dependency Checker) is a **Qos Measurement & Dependency Graph Platform**
created by OVH. We use it to store and request our CMDB and to compute the QoS
of our infrastructure, including our customers.

Overview
--------

.. figure:: _static/images/qos_dependencies.png
   :alt: Dependencies QOS

DepC provides a CMDB component to store and request related nodes into a graph
structure. These nodes can be anything : servers, products, customers or even
web services. A typical use case would be to create some ``customers`` nodes,
related to their ``products``. We can also link these ``products`` to
``servers``. that way it would be very easy to display the impacted customers
when a problem occurs on a server.

Once DepC knows your dependency graph, it then becomes possible to compute a
QoS for every nodes. By taking up our previous example, Depc can compute the
QoS of our ``customers``, following the QoS of their ``servers``.

.. note::
   QoS is not the same as SLA : please read :ref:`this guide <difference-qos-sla>`
   to view the difference between them. Notions about SLO and Indicators (used by
   DepC to compute the QoS) are also explained in it.

Principles
----------

- **Graph Dependency** : We use the *Neo4j* database to manage the nodes and
  their relationships (we already handle several million of nodes in our OVH
  internal instance). DepC provides some API calls and WebUI to easily request
  a node and its relations.
- **QoS Computation** : DepC can compute a QoS for all nodes in the Graph, but
  of course we must tell it how to do this. We created :ref:`different methods
  <queries>` for that : some nodes will use the raw data stored in TimeSeries
  databases (for example a ``server`` node having a probe), other nodes will
  use their parents QoS to compute their own one. Finally the QoS can be
  displayed in Grafana or in the DepC WebUI (this last allows some cool
  features, like display the worst nodes or even the root cause of a bad QoS).
- **Scalability** : *Apache Kafka* is used to receive :ref:`payload <kafka>`
  and forward them to Neo4j, adding the wanted scalabily and high-availability
  management. Then *Apache Airflow* is responsible to automate the QoS
  computation, so DepC can benefit from its executors feature (Celery,
  Kubernetes..) to scale horizontally.

And Next ?
----------

You can now install your own DepC instance following this :ref:`this link
<installation>`.

The simple way to test the most features is to follow the :ref:`quickstart
<quickstart>`. Then you can read the :ref:`guides <guides>` for the advanced
features and to understand how DepC works internally.
