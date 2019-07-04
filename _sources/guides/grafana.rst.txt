.. _grafana:

Grafana
=======

DepC provides two templates to bootstrap Grafana dashboards with information
concerning your QoS.

Installation
------------

.. warning::
    You have to be manager of your team to use this feature.

You must create the DepC source in your Grafana instance using the ``direct``
access.

You must also create the ``token`` constant containing your read-only token.
You can display it when you open a view throught the **Export to Grafana**
button available in your DepC homepage :

.. figure:: ../_static/images/guides/grafana/export_button.png
   :alt: Export Button
   :align: center

.. figure:: ../_static/images/guides/grafana/export_modal.png
   :alt: Export Modal
   :align: center

You can now copy the JSON of your wanted view (repeat the following
operation for each view) and paste it in Grafana using the **Import**
menu :

.. figure:: ../_static/images/guides/grafana/import_json.png
   :alt: Import JSON
   :align: center

.. figure:: ../_static/images/guides/grafana/import_json_2.png
   :alt: Import JSON
   :align: center

.. note::
    We only provide Warp10 export for now.

Summary view
------------

This dashboard displays your average QoS and the evolution of each
label. You can also quickly view the worst days by label.

.. figure:: ../_static/images/guides/grafana/summary.png
   :alt: QoS Summary


Details view
------------

You can use this dashboard to display the evolution of a specific node,
filtering it by label and by name.

.. figure:: ../_static/images/guides/grafana/details.png
   :alt: QoS Details

