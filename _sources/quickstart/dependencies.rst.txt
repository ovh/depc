.. _dependencies:

Step 1 : Push your Dependencies
===============================

DepC uses **Kafka** to handle messages and manage your dependencies
inside the Neo4j database :

-  Producer side : you send JSON messages in your dedicated topic to
   create your nodes and their relationships,
-  Consumer side : DepC reads your messages, validates them and updates
   your graph **in real time**.

.. note::
   The format of the Kafka messages is defined in this
   :ref:`dedicated guide <kafka>`, please read it to know the
   required and optionals keys.

We are going to create 7 nodes and their relationships : 2 **Website**,
2 **Filer**, 2 **Apache** and 1 **Offer**. We’ll use this simple Python
script to easily send our message in the Kafka topic, but of course you
can use your own library / language :

.. code:: python

   import json
   import os
   import ssl

   from kafka import KafkaProducer

   conf = {
       'bootstrap_servers': os.getenv('DEPC_KAFKA_HOST'),
       'security_protocol': 'SASL_SSL',
       'sasl_mechanism': 'PLAIN',
       'sasl_plain_username': os.getenv('DEPC_KAFKA_USERNAME'),
       'sasl_plain_password': os.getenv('DEPC_KAFKA_PASSWORD'),
       'ssl_context': ssl.SSLContext(ssl.PROTOCOL_SSLv23),
       'ssl_check_hostname': False,
       'client_id': os.getenv('DEPC_KAFKA_TOPIC'),
       'value_serializer': lambda v: json.dumps(v).encode('utf-8')
   }
   p = KafkaProducer(**conf)

   messages = [
       # Nodes for the Premium offer
       {'source': {'label': 'Offer', 'name': 'premium'}, 'target': {'label': 'Website', 'name': 'foo.com'}},
       {'source': {'label': 'Offer', 'name': 'premium'}, 'target': {'label': 'Website', 'name': 'bar.com'}},
       # Nodes for foo.com
       {'source': {'label': 'Website', 'name': 'foo.com'}, 'target': {'label': 'Filer', 'name': 'filer1'}},
       {'source': {'label': 'Website', 'name': 'foo.com'}, 'target': {'label': 'Apache', 'name': 'apache1'}},
       # Nodes for bar.com
       {'source': {'label': 'Website', 'name': 'bar.com'}, 'target': {'label': 'Filer', 'name': 'filer2'}},
       {'source': {'label': 'Website', 'name': 'bar.com'}, 'target': {'label': 'Apache', 'name': 'apache2'}}
   ]

   for m in messages:
       p.send(os.getenv('DEPC_KAFKA_TOPIC'), m)
   p.flush()

After executing it (don’t forget to set your environment variables), you
can display the new nodes in the **Dependencies** tab :

.. figure:: ../_static/images/quickstart/dependencies1.png
   :alt: Dependencies Tab

You can click on a label and search a specific node to display its
dependencies :

.. figure:: ../_static/images/quickstart/dependencies2.png
   :alt: Dependencies Graph

.. note::
   You can remove the nodes and their relationships with
   the **Delete node** button when you’re done with this quickstart.
