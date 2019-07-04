.. _quickstart:

Quickstart
==========

.. toctree::
   :hidden:
   :titlesonly:
   :maxdepth: 2

   dependencies
   qos
   configuration
   dashboard

.. note::
   The goal of this quickstart is to show you the main
   usage of DepC : manage your dependencies and compute their QOS.

**The Context**

We are member of the ACME team. Our role is to host the websites of our
customers. So we manage the storage of their files and some web servers.

**The Graph Model**

We split our nodes into four different categories : **Offer**,
**Webhosting**, **Filer** and **Apache**. In DepC a category is called a
**label** (this term comes directly from the Neo4J
`terminology <https://neo4j.com/docs/developer-manual/current/introduction/graphdb-concepts/#graphdb-neo4j-labels>`__).

The relationships between our labels are represented with the following
graph :

.. mermaid::
   :align: center

   graph TB;
       A(Offer)-->B(Website);
       B-->C(Filer);
       B-->D(Apache);

**Create your Team**

Most actions in DepC are done within a team, so you must already be part
of one or multiple team to play with DepC. A user can be a member, an
editor or a manager of a team.

.. warning::
   Only DepC administrators can create new teams for
   now, so please ask your admin to do it.

Once your team is created, you’ll be able to find it on the DepC home
page :

.. figure:: ../_static/images/quickstart/acme_team.png
   :alt: Acme Team
   :align: center
