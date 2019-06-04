import pytest

from depc.controllers.teams import TeamController


def test_generate_marmaid_diagram_simple(app):
    configs = {"Apache": {"qos": "rule.Servers"}}

    with app.app_context():
        query = TeamController()._generate_marmaid_diagram(configs)

    assert query == "graph TB\\n\\ndepc.qos.label_name_Apache_[Apache]\\n"


def test_generate_marmaid_diagram_advanced(app):
    configs = {
        "Apache": {"qos": "rule.Servers"},
        "Filer": {"qos": "rule.Servers"},
        "Offer": {"qos": "aggregation.AVERAGE[Website]"},
        "Website": {"qos": "operation.AND[Filer, Apache]"}
    }

    with app.app_context():
        query = TeamController()._generate_marmaid_diagram(configs)

    assert "graph TB\\n\\n" in query
    assert "depc.qos.label_name_Filer_[Filer]\\n" in query
    assert "depc.qos.label_name_Apache_[Apache]\\n" in query
    assert "depc.qos.label_name_Website_[Website] --> depc.qos.label_name_Filer_[Filer]\\n" in query
    assert "depc.qos.label_name_Website_[Website] --> depc.qos.label_name_Apache_[Apache]\\n" in query
    assert "depc.qos.label_name_Offer_[Offer] --> depc.qos.label_name_Website_[Website]\\n" in query
