Variables
=========

DepC allows you to declare a variable that can be reused in
your **checks parameters**.

A variable can be of the following types :

-  a string
-  a text
-  a number

You can create it in the **Variables** menu within your team, for
example :

.. figure:: ../_static/images/guides/variables/check_variable.png
   :alt: Check Variable

Here we declare a variable in the **Check** level : it means that
``{{ depc.check.location }}`` will be replaced by the *FR2* value in all
uses.

Levels
------

To be as flexible as possible, DepC supports 4 levels of variables :

-  Team : ``{{ depc.team.myTeamVar }}``
-  Rule : ``{{ depc.rule.myRuleVar }}``
-  Source : ``{{ depc.source.mySourceVar }}``
-  Check : ``{{ depc.check.myCheckVar }}``

Builtins Variables
------------------

By default 3 builtins variables are available :

-  Name : ``{{ depc.name }}``
-  Start: ``{{ depc.start }}``
-  End: ``{{ depc.end }}``

These variables represent the 3 arguments sent to every checks when
launching a rule :

.. figure:: ../_static/images/guides/variables/builtins_variables.png
   :alt: Builtins Variables

Jinja2 Templating
-----------------

After declaring it, you can reuse your variables with the
`Jinja2 <http://jinja.pocoo.org/docs/>`__ syntax (calling the variables
can be done within the ``{{ ... }}`` delimiters).

.. note::
   You can use the **iso8601** filter after your
   timestamp variables : it will convert the timestamp into its iso8601
   value (``{{ depc.start | iso8601 }}``).

You can also use the Jinja2 conditions. For example your can filter your
timeseries by tags if the name was sent during the rule execution :

.. figure:: ../_static/images/guides/variables/jinja_condition_1.png
   :alt: Jinja Condition 1

.. figure:: ../_static/images/guides/variables/jinja_condition_2.png
   :alt: Jinja Condition 2

.. figure:: ../_static/images/guides/variables/jinja_condition_3.png
   :alt: Jinja Condition 3

