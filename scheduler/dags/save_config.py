import datetime
import logging

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python_operator import PythonOperator

from scheduler.dags import app, get_records

logger = logging.getLogger(__name__)


default_args = {
    "owner": "depc",
    "start_date": datetime.datetime(2019, 1, 1),
    "retries": 1,
    "retry_delay": datetime.timedelta(minutes=5),
}


dag = DAG(dag_id="config", default_args=default_args, schedule_interval="0 1 * * *")


def get_teams_schema(ds, **kwargs):
    """
    This task lists the last config for every team. Then a Neo4j
    query is done to count the nodes of each label.
    """
    with kwargs["params"]["app"].app_context():
        from depc.controllers.configs import ConfigController

        # Get all configs ordered by -date
        configs = ConfigController._list(order_by="updated_at", reverse=True)

        # Get the last config by team
        teams = {}
        for config in configs:

            team = config.team

            # For each team
            if team.kafka_topic not in teams.keys():
                logger.info("[{0}] Configuration : {1}".format(team.name, config.data))

                data = {
                    "id": team.id,
                    "name": team.name,
                    "topic": team.kafka_topic,
                    "schema": config.data,
                    "labels": {},
                }

                # Count number of nodes per label
                logger.info(
                    "[{0}] Counting nodes for {1} labels...".format(
                        team.name, len(config.data.keys())
                    )
                )

                for label in config.data.keys():
                    neo_key = "{}_{}".format(team.kafka_topic, label)
                    records = get_records(
                        "MATCH (n:{label}) RETURN count(n) AS Count".format(
                            label=neo_key
                        )
                    )
                    count = list(records)[0].get("Count")

                    logger.info(
                        "[{0}] {1} nodes for label {2}...".format(
                            team.name, count, label
                        )
                    )
                    data["labels"][label] = count

                teams[team.kafka_topic] = data

        # Save the config into an Airflow variable
        Variable.set("config", list(teams.values()), serialize_json=True)


PythonOperator(
    task_id="save",
    dag=dag,
    provide_context=True,
    python_callable=get_teams_schema,
    params={"app": app},
)
