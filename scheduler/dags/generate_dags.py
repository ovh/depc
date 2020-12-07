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


def generate_chunked_tuples(count, chunk_size=1000):
    """
    Generate the "SKIP" values and "LIMIT" values for the Neo4j queries
    :param count: number of items to chunk
    :param chunk_size: size of a chunk (default: 1000)
    :return: list of tuples with two values (skip, limit)
    """
    if count <= chunk_size:
        return [(0, count)]

    nb_chunks = count // chunk_size
    nb_orphans = count % chunk_size

    skips = range(0, nb_chunks * chunk_size + chunk_size, chunk_size)
    limits = [chunk_size for _ in range(nb_chunks)]

    middle = chunk_size / 2
    if nb_orphans <= middle:
        limits[len(limits) - 1] = chunk_size + nb_orphans
    elif nb_orphans > middle:
        limits.append(nb_orphans)

    return [(s, l) for s, l in zip(skips, limits)]


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

    tasks = []
    for skip, length in generate_chunked_tuples(count):
        chunk_name = "{}.chunk.{}".format(label, skip)
        # All custom operators share these parameters
        params = {
            "app": app,
            "team": team,
            "label": label,
            "skip": skip,
            "length": length,
            **operator_params,
        }
        tasks.append(fn(task_id=chunk_name, dag=dag, params=params))

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


teams = Variable.get("config", default_var=[], deserialize_json=True)
# You need to go on the Variables page of the Airflow Web UI, e.g.: http://localhost:8080/admin/variable/
# then create a new Variable with a key "schedule" and for value, e.g.: {"slug_of_the_team": "15 2 * * *"}
custom_schedule_intervals = Variable.get(
    "schedule", default_var={}, deserialize_json=True
)
# Create the DAGs
for team in teams:
    try:
        team_schedule_interval = custom_schedule_intervals.get(
            team["topic"], schedule_interval
        )
        globals()[team["topic"]] = create_dag(
            team, team_schedule_interval, default_args
        )
    except Exception as e:
        logger.error(
            "Exception in team {team} : {exc}".format(team=team["name"], exc=str(e))
        )
