Installation
============


Preamble
~~~~~~~~

In order to fully run DepC you have to follow several steps described below.
Also, you need to setup your environment with these following software :

- `Redis <https://redis.io/topics/quickstart>`__
- `Kafka (1.1.0) <https://kafka.apache.org/11/documentation.html#quickstart>`__
- `Neo4j (3.4) <https://nodejs.org/en/download/releases/>`__
- A RDBMS supported by SQLAlchemy (we suggest `PostgreSQL <https://www.postgresql.org/download/>`__)
- The `Warp10 <https://www.warp10.io/content/02_Getting_started>`__ time series database

Take a look on the ``depc.example.yml`` to set the required configuration fields accordingly.

.. note::
    Even if DepC supports also OpenTSDB to compute the QOS, it currently requires the Warp10 database
    to store its own metrics. We are working to make Warp10 optional to run DepC.

.. warning::

    We are aware this installation guide requires multiple manual configuration steps.
    We plan to improve the installation process in a future release.


Create your virtual environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You may need to install Python 3.5+ first, this step can differ depending on your operating system,
please refer to the official `Python documentation <https://docs.python.org/3/using/index.html>`__
for further details.

.. code:: bash

    pip install virtualenv
    virtualenv -p python3 venv
    source venv/bin/activate


Install the requirements
~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: bash

    pip install -r requirements.txt


Configure your environment
~~~~~~~~~~~~~~~~~~~~~~~~~~
In DepC the root directory, you have to create a new configuration file for your environment
using the provided configuration sample in ``depc.example.yml``.
Name the configuration file ``depc.<env>.yml`` where you should replace ``<env>`` with the
``DEPC_ENV`` value.

Set these environment variables :

.. code:: bash

    export DEPC_HOME="$(pwd)"

    # Then export, one of the following environment variable

    # Development environment will use a depc.dev.yml file
    export DEPC_ENV=dev

    # Testing environment will use a depc.test.yml file
    export DEPC_ENV=test

    # Production environment will use a depc.prod.yml file
    export DEPC_ENV=prod


Launch the API
~~~~~~~~~~~~~~

Using the Flask development server :

.. code:: bash

    make api

Using Gunicorn :

.. code:: bash

    gunicorn --bind 0.0.0.0:5000 manage:app


Now you can reach the API to this URL :

.. code:: bash

    curl http://localhost:5000/v1/ping

You should have this response :

.. code:: json

    {
      "message": "pong"
    }


.. note::

    During development, you may want to create a new team, grant users, etc...
    To force the access to the DepC admin panel at: ``http://localhost:5000/admin``.
    Put the ``FORCE_INSECURE_ADMIN: true`` value into your configuration file.


Setup the Web UI
~~~~~~~~~~~~~~~~

To install and run the Web UI you need to install `Node.js 8 <https://nodejs.org/en/download/releases/>`__.
Then you will be able to run the NPM command-line tool packaged with your Node.js installation.

In the ``ui/`` directory :

.. code:: bash

    npm install
    npm install bower grunt grunt-cli -g
    bower install

.. note::

    In your development environment, you need to fake the authentication gateway, in this case,
    edit the file ``app/scripts/services/httpinterceptor.js`` and lookup for the line below.
    Uncomment this line and replace ``username`` with your own desired user.

    .. code:: javascript

        // config.headers['X-Remote-User'] = 'username';


To start the Web UI :

.. code:: bash

    make ui

Now, you ca reach the DepC Web UI at : ``http://localhost:9000/#/teams``

Setup Airflow
~~~~~~~~~~~~~

To get more details about how to setup Airflow,
please read the `official documentation <https://airflow.apache.org/index.html>`__.

.. code:: bash

    # Add the DepC root directory to the PYTHONPATH
    export PYTHONPATH="$(pwd)/:$PYTHONPATH"

    # Specify the DepC scheduler directory as the Airflow root directory
    export AIRFLOW_HOME="$(pwd)/scheduler"

    # Before this step, remember, you have to generate/configure the airflow.cfg
    make webserver

    # In another terminal
    make scheduler


Start the Kafka consumer
~~~~~~~~~~~~~~~~~~~~~~~~

You have to configure the appropriate fields into your configuration file (section ``CONSUMER``).

.. code:: bash

    make consumer
