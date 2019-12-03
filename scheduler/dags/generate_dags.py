import datetime
import logging
import math
import re

from airflow import DAG
from airflow.executors import get_default_executor
from airflow.models import Variable
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator
from airflow.operators.subdag_operator import SubDagOperator

from scheduler.dags import app
from scheduler.dags.operators import delete_redis_avg
from scheduler.dags.operators.after_subdag_operator import AfterSubdagOperator
from scheduler.dags.operators.aggregation_operator import AggregationOperator
from scheduler.dags.operators.average_operator import AverageOperator
from scheduler.dags.operators.before_subdag_operator import BeforeSubdagOperator
from scheduler.dags.operators.daily_worst_operator import DailyWorstOperator
from scheduler.dags.operators.operation_operator import OperationOperator
from scheduler.dags.operators.rule_operator import RuleOperator

logger = logging.getLogger(__name__)


default_args = {
    "owner": "depc",
    "start_date": datetime.datetime(2019, 1, 1),
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}
schedule_interval = "15 1 * * *"


operators = {
    "rule": RuleOperator,
    "operation": OperationOperator,
    "aggregation": AggregationOperator,
}


def find_label_operator(query):
    """
    Use regex to find the good operator.

    Rule examples:
        rule.Foobar
        rule.foo
        rule.'Foo bar'

    Operation examples:
        operation.AND()[Foo, Bar]
        operation.OR[Foo, Bar]
        operation.OR()[Foo, Bar]
        operation.AND()[Foo]
        operation.AND[Foo]
        operation.AND[A, B, C]
        operation.OR()[A]
        operation.OR[A]
        operation.OR()[A, B]
        operation.RATIO(0.35)[Foo]
        operation.RATIO(0.35)[Foo, Bar]
        operation.ATLEAST(10)[Foo]
        operation.ATLEAST(10)[Foo, Bar]

    Aggregation examples:
        aggregation.AVERAGE[Foo, Bar]
        aggregation.MAX()[Foo]
        aggregation.MIN()[Foo, Bar]
        aggregation.MIN[Foo, Bar]

    TODO 1 : Use a lexer more robust (http://www.dabeaz.com/ply/index.html)
    TODO 2 : Reuse these regex for the jsonschema used in the API
    """
    # If you apply any changes into these regex patterns, please update the JSON schema consequently at:
    # depc/schemas/v1_config.json
    # Rule
    regex = r"^rule.(.+|'.+')$"
    match = re.search(regex, query)
    if match:
        rule = match.group(1)
        if rule.startswith("'"):
            rule = rule[1:-1]
        return RuleOperator, {"rule": rule}

    # Operation AND, OR (no argument)
    regex = (
        r"^operation.(AND|OR)\(?\)?(\[[A-Z]+[a-zA-Z0-9]*(, [A-Z]+[a-zA-Z0-9]*)*?\])$"
    )
    match = re.search(regex, query)
    if match:
        # Transform '[Foo, Bar]' into a Python list
        deps = match.group(2)[1:-1].split(", ")
        return OperationOperator, {"type": match.group(1), "dependencies": deps}

    # Operation ATLEAST (integer argument)
    regex = r"^operation.(ATLEAST\([0-9]+\))(\[[A-Z]+[a-zA-Z0-9]*(, [A-Z]+[a-zA-Z0-9]*)*?\])$"
    match = re.search(regex, query)
    if match:
        deps = match.group(2)[1:-1].split(", ")
        return OperationOperator, {"type": match.group(1), "dependencies": deps}

    # Operation RATIO (float integer less than 0)
    regex = r"^operation.(RATIO\(0.[0-9]+\))(\[[A-Z]+[a-zA-Z0-9]*(, A-Z]+[a-zA-Z0-9]*)*?\])$"
    match = re.search(regex, query)
    if match:
        deps = match.group(2)[1:-1].split(", ")
        return OperationOperator, {"type": match.group(1), "dependencies": deps}

    # Aggregation AVERAGE, MIN, MAX
    regex = r"^aggregation.(AVERAGE|MIN|MAX)\(?\)?(\[[A-Z]+[a-zA-Z0-9]*(, [A-Z]+[a-zA-Z0-9]*)*?\])$"
    match = re.search(regex, query)
    if match:
        deps = match.group(2)[1:-1].split(", ")
        return AggregationOperator, {"type": match.group(1), "dependencies": deps}

    # We validate the schema before save it in database,
    # it's not possible to go here.
    return None, None


def create_subdag(dag_parent, label, team):
    dag_id_child = "%s.%s" % (dag_parent.dag_id, label)
    schema = team["schema"][label]

    dag = DAG(
        dag_id=dag_id_child,
        default_args=dag_parent.default_args,
        schedule_interval=dag_parent.schedule_interval,
    )

    # Find the corresponding operator and its parameters
    fn, operator_params = find_label_operator(schema["qos"])

    # Label is declared but there is no node in Neo4j
    count = team["labels"][label]
    if not count:
        DummyOperator(task_id="{}.notask".format(label), dag=dag)
        return dag, operator_params.get("dependencies")

    if count < 100:
        length = count
    else:
        frac, length = math.modf(count / 100)
        if frac:
            length += 1

    chunks = {"{}.chunk.{}".format(label, i): i for i in range(0, count, int(length))}

    tasks = []
    for name, skip in chunks.items():

        # All custom operators share these parameters
        params = {
            "app": app,
            "team": team,
            "label": label,
            "skip": skip,
            "length": length,
            **operator_params,
        }

        tasks.append(fn(task_id=name, dag=dag, params=params))

    with dag:
        delete_redis_avg_op = PythonOperator(
            task_id="{}.del_redis_average".format(label),
            provide_context=True,
            python_callable=delete_redis_avg,
            params={"app": app, "team": team, "label": label},
        )

        before_subdag_task = BeforeSubdagOperator(
            task_id="{}.before_subdag".format(label),
            params={
                "app": app,
                "team": team,
                "label": label,
                "count": count,
                "excluded_nodes_from_average": schema.get("label", {}).get(
                    "average.exclude"
                ),
            },
        )

        after_subdag_task = AfterSubdagOperator(
            task_id="{}.after_subdag".format(label),
            params={"app": app, "team": team, "label": label},
        )

        after_chunks_task = DummyOperator(task_id="{}.dummy".format(label))

        average_op = AverageOperator(
            task_id="{}.average".format(label),
            params={"app": app, "team": team, "label": label},
        )

        daily_worst_op = DailyWorstOperator(
            task_id="{}.daily_worst".format(label),
            params={"app": app, "team": team, "label": label},
        )

    before_subdag_task.set_downstream(delete_redis_avg_op)
    delete_redis_avg_op.set_downstream(tasks)
    after_chunks_task.set_upstream(tasks)
    after_chunks_task.set_downstream([average_op, daily_worst_op])
    after_subdag_task.set_upstream([average_op, daily_worst_op])

    return dag, operator_params.get("dependencies")


def create_subdag_operator(dag_parent, label, team):
    subdag, dependencies = create_subdag(dag_parent, label, team)

    # Since v1.10, Airflow forces to use the SequentialExecutor as the default
    # executor for the SubDagOperator, so we need to explicitly specify the
    # executor from the airflow.cfg
    sd_op = SubDagOperator(
        task_id=label, dag=dag_parent, subdag=subdag, executor=get_default_executor()
    )
    return sd_op, dependencies


def create_dag(team, schedule_interval, default_args):
    dag = DAG(
        team["topic"], schedule_interval=schedule_interval, default_args=default_args
    )

    with dag:
        subdags = {}

        # First step : create the tasks
        for label in team["schema"].keys():
            sd_op, deps = create_subdag_operator(dag, label, team)
            subdags[label] = {"op": sd_op, "dependencies": deps}

        # Second step : link them
        for label, data in subdags.items():
            deps = data["dependencies"]
            if deps:
                subdags[label]["op"].set_upstream([subdags[l]["op"] for l in deps])

    return dag


# Create the DAGs
teams = Variable.get("config", default_var=[], deserialize_json=True)
if not teams:
    logger.error("Configuration has not been saved.")
else:
    for team in teams:
        try:
            globals()[team["topic"]] = create_dag(team, schedule_interval, default_args)
        except Exception as e:
            logger.error(
                "Exception in team {team} : {exc}".format(team=team["name"], exc=str(e))
            )
