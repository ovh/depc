.. sources:

Sources Configuration
=====================

DepC currently supports 2 TimeSeries databases : **OpenTSDB** and **Warp10**.

OpenTSDB
--------

OpenTSDB is a scalable and distributed time series database. Please refer to
the `official documentation <http://opentsdb.net/docs/build/html/index.html>`__
to learn how to query OpenTSDB.

DepC needs 2 informations to query an OpenTSDB database :

- an url : ``http://my-opentsdb.local``
- the credentials separated by a colon : ``myuser:mypassword``

Here is a really simple payload, to show you how to use it in your checks :

.. code:: json

    {
        "tags": {
            "name": "{{ depc.name }}"
        },
        "aggregator": "avg",
        "metric": "my.awesome.metric"
    }


Warp10
------

Warp10 is a Geo Time Series database. DepC uses the ``/exec`` endpoint to
query it, so please refer to the `official documentation
<https://www.warp10.io/content/03_Documentation/04_WarpScript/01_Concepts>`__
to learn how to query Warp10.

DepC needs 2 informations to query a Warp10 database :

- an url containing the API version : ``http://my-warp10.local/api/v0``
- a read-only token : ``myrotoken``

Here is a really simple payload, to show you how to use it in your checks :

.. code::

    [   $token
        'my.awesome.metric'
        {  'name'  '{{ depc.name }}' }
        $start $end
    ] FETCH SORT

As you can see you can access 3 variables populated by DepC when launching
your check :

- ``$token`` : the token provided in the source configuration,
- ``$start`` : the start time of the analysed period, in ISO8601 format,
- ``$end`` : the end time of the analysed period, in ISO8601 format.
