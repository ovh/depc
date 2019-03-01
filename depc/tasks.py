import time
from datetime import datetime

from flask import json
from jinja2.exceptions import TemplateError
from loguru import logger

from depc.extensions import redis
from depc.sources import BaseSource
from depc.sources.exceptions import UnknownStateException, BadConfigurationException

from depc.templates import Template
from depc.utils.qos import compute_qos_from_bools


def write_log(logs, message, level):
    data = {"created_at": datetime.now(), "message": message, "level": level}
    getattr(logger, level.lower())(message)
    logs.append(data)
    return logs


async def execute_asyncio_check(check, name, start, end, key, variables):
    logs = []
    logs = write_log(
        logs, "[{0}] Executing check ({1})...".format(check.name, check.id), "INFO"
    )

    source = check.source
    source_plugin = BaseSource.load_source(source.plugin, source.configuration)
    logs = write_log(
        logs, "[{0}] Raw parameters : {1}".format(check.name, check.parameters), "INFO"
    )

    template = Template(
        check=check,
        context={"name": name, "start": start, "end": end, "variables": variables},
    )

    start_time = time.time()
    error = None
    check_result = None

    try:
        parameters = template.render()
    except TemplateError as e:
        parameters = {}
        error = e
        logs = write_log(logs, "[{0}] {1}".format(check.name, str(error)), "ERROR")
    else:
        logs = write_log(
            logs,
            "[{0}] Rendered parameters : {1}".format(check.name, parameters),
            "DEBUG",
        )

        check_plugin = source_plugin.load_check(
            check_name=check.type,
            parameters=parameters,
            name=name,
            start=start,
            end=end,
        )
        try:
            check_result = await check_plugin.execute()
        except UnknownStateException as e:
            error = e
            logs = write_log(logs, "[{0}] {1}".format(check.name, str(error)), "ERROR")
        except (BadConfigurationException, Exception) as e:
            error = e
            logs = write_log(logs, "[{0}] {1}".format(check.name, str(error)), "ERROR")

    # Display check duration
    duration = time.time() - start_time
    logs = write_log(
        logs, "[{0}] Check duration : {1}s".format(check.name, duration), "INFO"
    )

    result = {
        "id": check.id,
        "name": check.name,
        "type": check.type,
        "parameters": parameters,
        "duration": duration,
        "qos": None,
    }

    if error or not check_result:
        result.update({"error": str(error)})
    else:
        result.update(check_result)

        if result["qos"]:
            logs = write_log(
                logs,
                "[{0}] Check returned {1}%".format(check.name, check_result["qos"]),
                "INFO",
            )
        else:
            logs = write_log(
                logs,
                "[{0}] No QOS returned by the check".format(
                    check.name, check_result["qos"]
                ),
                "INFO",
            )

    return {"logs": logs, "result": result}


def merge_all_checks(checks, rule, key, context):
    result = {"context": context, "logs": []}

    # Remove the result key
    checks_copy = [c["result"] for c in checks]
    result["checks"] = checks_copy

    # Merge the logs
    for check in checks:
        result["logs"].extend(check.pop("logs"))

    # Remove check with no QOS
    checks_copy = [c for c in checks_copy if c["qos"] is not None]

    if checks_copy:
        result_rule = compute_qos_from_bools(
            booleans=[c["bools_dps"] for c in checks_copy]
        )
        result.update(result_rule)

        result["logs"] = write_log(
            result["logs"], "[{0}] Rule done".format(rule.name), "INFO"
        )
        result["logs"] = write_log(
            result["logs"],
            "[{0}] Rule QOS is {1:.5f}%".format(rule.name, result["qos"]),
            "INFO",
        )
    else:
        result["qos"] = "unknown"
        result["logs"] = write_log(
            result["logs"],
            "[{0}] No QOS was found in any checks, so no QOS can be computed for the rule".format(
                rule.name
            ),
            "INFO",
        )

    # Add the check details in the result
    redis.set(
        key, json.dumps(result).encode("utf-8"), ex=redis.seconds_until_midnight()
    )
    result["logs"] = write_log(
        result["logs"],
        "[{0}] Result added in cache ({1})".format(rule.name, key),
        "INFO",
    )

    return result
