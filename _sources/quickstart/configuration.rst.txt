Step 3 : Create the Configuration
=================================

Now that :ref:`we have pushed <dependencies>` our nodes and
:ref:`created the rule <qos>` to compute the QoS of our servers, we must
indicate how to compute the QoS for each kind of nodes.

Depending on whether you have metrics to analyze or not, DepC can use 2
methods to compute the QoS of a node :

1. analysing datapoints available in a TimeSeries database,
2. using the QoS of its parent(s).

As a reminder the ACME team has 4 labels :

.. mermaid::
   :align: center

   graph TB;
      A(Offer)-->B(Website);
      B-->C(Filer);
      B-->D(Apache);

In this quickstart the QoS of the **Apache** and **Filer** nodes
will be computed by analysing TimeSeries database.

The **Website** nodes will use it to compute their own QoS, and the
**Offer** nodes will compute their QoS by doing an average of their
children's QoS.

This information is given in the team’s configuration using a **JSON
representation** :

.. code:: json

   {
    "Apache": {
     "qos": "rule.Servers"
    },
    "Filer": {
     "qos": "rule.Servers"
    },
    "Offer": {
     "qos": "aggregation.AVERAGE[Website]"
    },
    "Website": {
     "qos": "operation.AND[Filer, Apache]"
    }
   }

Go to the **Configuration** tab of your team, click on the **Update the
configuration** button and fill it with this JSON :

.. figure:: ../_static/images/quickstart/update_configuration.png
   :alt: Update Configuration

As you can see there is a graph near your configuration : it’s a visual
representation of how DepC will compute your QOS for your nodes. In this
case the workflow will be the following :

1. First DepC will compute the QoS of the **Filer** and **Apache** nodes
   (in parallel) using the **Servers** rule (more on this in the :ref:`next step <qos>`).
2. Then DepC will compute the QoS of the **Website** nodes by applying a AND
   operation between their parents (more on this in the :ref:`dedicated guide <queries>`).
3. Finally DepC will compute the QoS of the **Offer** nodes using the average of their
   parents QoS.

You can now display the rules in the **Dependencies** tab :

.. figure:: ../_static/images/quickstart/dependencies_with_rules.png
   :alt: Update Configuration
   :align: center

.. note::
   You can find more information about the different methods to compute
   a QOS and their syntax in the :ref:`dedicated guide <queries>`.
