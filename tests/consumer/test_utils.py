import json

import fastjsonschema
import pytest
from fastjsonschema.exceptions import JsonSchemaException

from consumer.kafka_consumer.utils import (DEFINITIONS_PATH,
                                           validate_flat_message,
                                           validate_nested_message)


@pytest.fixture
def validate():
    def _validate(key, value):
        with open(DEFINITIONS_PATH, "r") as f:
            schemas = json.load(f)

        # Need to copy label and name definitions in the node
        schemas['definitions']['node']['definitions'] = {
            'label': schemas['definitions']['label'],
            'name': schemas['definitions']['name'],
            'from': schemas['definitions']['from'],
            'to': schemas['definitions']['to']
        }

        val = fastjsonschema.compile(schemas['definitions'][key])
        return val(value)
    return _validate


@pytest.mark.parametrize("payload", [
    "MyLabel", "Mylabel", "My123Label",
    "MyLabel123", "My12Label3"
])
def test_validation_label_success(payload, validate):
    assert validate("label", payload) == payload


@pytest.mark.parametrize("payload", [
    "mylabel", "myLabel", "My#Label{}"
    "123Label", " ", ""
])
def test_validation_label_error(payload, validate):
    with pytest.raises(JsonSchemaException):
        validate("label", payload)


@pytest.mark.parametrize("payload", [
    "Foo", "foo", "foo123bar", "#F$o%ob&a-r.", "#F$o%ob&/a-r."
])
def test_validation_name_success(payload, validate):
    assert validate("name", payload) == payload


@pytest.mark.parametrize("payload", [
    "foo bar", "foo'bar", 'foo"bar', "foo\bar",
    "foo`bar", " ", ""
])
def test_validation_name_error(payload, validate):
    with pytest.raises(JsonSchemaException):
        validate("name", payload)


@pytest.mark.parametrize("payload", [
    0, 100, 10000
])
def test_validation_from_success(payload, validate):
    assert validate("from", payload) == payload


@pytest.mark.parametrize("payload", [
    "foo", -100
])
def test_validation_from_error(payload, validate):
    with pytest.raises(JsonSchemaException):
        validate("from", payload)


@pytest.mark.parametrize("payload", [
    1, 100, 10000
])
def test_validation_to_success(payload, validate):
    assert validate("to", payload) == payload


@pytest.mark.parametrize("payload", [
    "foo", 0, -100
])
def test_validation_to_error(payload, validate):
    with pytest.raises(JsonSchemaException):
        validate("to", payload)


@pytest.mark.parametrize("payload", [
    {"label": "Mylabel", "name": "foo"},
    {"label": "Mylabel", "name": "foo", "props": {"from": 0}},
    {"label": "Mylabel", "name": "foo", "props": {"to": 1}},
    {"label": "Mylabel", "name": "foo", "props": {"from": 0, "to": 1}}
])
def test_validation_node_success(payload, validate):
    assert validate("node", payload) == payload


@pytest.mark.parametrize("payload", [
    {"label": "MyLabel"},
    {"name": "foo"},
    {"label": "MyLabel", "name": "foo", "additional": "property"}
])
def test_validation_node_error(payload, validate):
    with pytest.raises(JsonSchemaException):
        validate("node", payload)


@pytest.mark.parametrize("payload", [
    {"source": {"label": "MyLabel", "name": "foo"}},
    {"source": {"label": "MyLabel", "name": "foo"}, "target": {"label": "MyLabel", "name": "bar"}},
    {"source": {"label": "MyLabel", "name": "foo"}, "target": {"label": "MyLabel", "name": "bar"}},
    {"source": {"label": "MyLabel", "name": "foo"}, "target": {"label": "MyLabel", "name": "bar"}, "rel": {"from": 0}},
    {"source": {"label": "MyLabel", "name": "foo"}, "target": {"label": "MyLabel", "name": "bar"}, "rel": {"to": 1}},
    {"source": {"label": "MyLabel", "name": "foo"}, "target": {"label": "MyLabel", "name": "bar"}, "rel": {"from": 0, "to": 1}},
])
def test_validation_nested_success(payload, validate):
    assert validate_nested_message(payload) == payload


@pytest.mark.parametrize("payload", [
    {},
    {"source": {}},
    {"sourcetypo": {"label": "MyLabel", "name": "foo"}},
    {"target": {"label": "MyLabel", "name": "foo"}},
    {"source": {"label": "MyLabel", "name": "foo"}, "additional": "property"},
])
def test_validation_nested_error(payload):
    with pytest.raises(JsonSchemaException):
        validate_nested_message(payload)


@pytest.mark.parametrize("payload", [
    {"source_label": "MyLabel", "source_name": "foo"},
    {"source_label": "MyLabel", "source_name": "foo", "source_from": 0, "source_to": 1},
    {"source_label": "MyLabel", "source_name": "foo", "target_label": "MyLabel", "target_name": "bar"},
    {
        "source_label": "MyLabel", "source_name": "foo", "source_from": 0, "source_to": 1,
        "target_label": "MyLabel", "target_name": "bar", "target_from": 0, "target_to": 1
    },
    {
        "source_label": "MyLabel", "source_name": "foo", "source_from": 0, "source_to": 1,
        "target_label": "MyLabel", "target_name": "bar", "target_from": 0, "target_to": 1,
        "rel_from": 0, "rel_to": 1
    }
])
def test_validation_flat_success(payload, validate):
    assert validate_flat_message(payload) == payload


@pytest.mark.parametrize("payload", [
    {},
    {"foo": "bar"},
    {"source_label": "MyLabel"},
    {"source_name": "foo"},
    {"target_label": "MyLabel", "target_name": "foo"},
    {"source_label": "MyLabel", "source_name": "foo", "additional": "property"}
])
def test_validation_flat_error(payload):
    with pytest.raises(JsonSchemaException):
        validate_flat_message(payload)
