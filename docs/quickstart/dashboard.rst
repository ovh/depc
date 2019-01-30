Step 4 : Play with the Dashboard
================================

DepC computes the QoS of your nodes every nights (for the day before) using
**Airflow**, and the result is available in the **Dashboard** tab. If
you followed this quickstart your dashboard must be empty.

If you wait some days, your dashboard will be like the following :

.. figure:: ../_static/images/quickstart/dashboard1.png
   :alt: Dashboard 1

By clicking on a label, you can select a specific node and analyses its
dependencies to understand where comes from a problem :

.. figure:: ../_static/images/quickstart/dashboard2.png
   :alt: Dashboard 2

Then you can *zoom* in the dependencies until you meet a rule-based
node, for example the **Apache** dependency. You can see what was the
problem by selecting a day and launch the rule :

.. figure:: ../_static/images/quickstart/dashboard3.png
   :alt: Dashboard 3
