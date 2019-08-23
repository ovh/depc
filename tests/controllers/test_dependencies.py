import pytest

from depc.controllers.dependencies import DependenciesController


class NodeMock:
    def __init__(self, node_data_dict):
        self._id = node_data_dict.get("id", 0)
        self._labels = node_data_dict.get("labels", {})
        self._properties = node_data_dict.get("properties", {})

    def __eq__(self, other):
        try:
            return type(self) == type(other) and self.id == other.id
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def __len__(self):
        return len(self._properties)

    def __getitem__(self, name):
        return self._properties.get(name)

    def __contains__(self, name):
        return name in self._properties

    def __iter__(self):
        return iter(self._properties)

    def __repr__(self):
        return "<Node id=%r labels=%r properties=%r>" % (self._id, self._labels, self._properties)

    @property
    def id(self):
        """ The identity of this entity in its container :class:`.Graph`.
        """
        return self._id

    @property
    def labels(self):
        return frozenset(self._labels)

    def _update(self, properties, **kwproperties):
        properties = dict(properties or {}, **kwproperties)
        self._properties.update((k, v) for k, v in properties.items() if v is not None)

    def get(self, name, default=None):
        """ Get a property value by name, optionally with a default.
        """
        return self._properties.get(name, default)

    def keys(self):
        """ Return an iterable of all property names.
        """
        return self._properties.keys()

    def values(self):
        """ Return an iterable of all property values.
        """
        return self._properties.values()

    def items(self):
        """ Return an iterable of all property name-value pairs.
        """
        return self._properties.items()


class RelationshipMock:
    def __init__(self, relationship_data_dict, start_node, end_node):
        self._id = relationship_data_dict.get("id", 0)
        self._start_node = start_node
        self._end_node = end_node
        self._type = relationship_data_dict.get("type", "")
        self._properties = relationship_data_dict.get("properties", {})

    def __eq__(self, other):
        try:
            return type(self) == type(other) and self.id == other.id
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def __len__(self):
        return len(self._properties)

    def __getitem__(self, name):
        return self._properties.get(name)

    def __contains__(self, name):
        return name in self._properties

    def __iter__(self):
        return iter(self._properties)

    def __repr__(self):
        return "<Relationship id=%r nodes=(%r, %r) type=%r properties=%r>" % (
            self._id, self._start_node, self._end_node, self.type, self._properties)

    @property
    def id(self):
        """ The identity of this entity in its container :class:`.Graph`.
        """
        return self._id

    @property
    def nodes(self):
        return self._start_node, self._end_node

    @property
    def start_node(self):
        return self._start_node

    @property
    def end_node(self):
        return self._end_node

    @property
    def type(self):
        return type(self).__name__

    def _update(self, properties, **kwproperties):
        properties = dict(properties or {}, **kwproperties)
        self._properties.update((k, v) for k, v in properties.items() if v is not None)

    def get(self, name, default=None):
        """ Get a property value by name, optionally with a default.
        """
        return self._properties.get(name, default)

    def keys(self):
        """ Return an iterable of all property names.
        """
        return self._properties.keys()

    def values(self):
        """ Return an iterable of all property values.
        """
        return self._properties.values()

    def items(self):
        """ Return an iterable of all property name-value pairs.
        """
        return self._properties.items()


offer01_data_dict = {
    "labels": {'acme_Offer'},
    "properties": {'from': 1566338400, 'name': 'offer01'}
}
offer01_node = NodeMock(offer01_data_dict)

website01_data_dict = {
    "labels": {'acme_Website'},
    "properties": {'from': 1566424800, 'name': 'website01'}
}
website01_node = NodeMock(website01_data_dict)

website02_data_dict = {
    "labels": {'acme_Website'},
    "properties": {'from': 1566079200, 'name': 'website02'}
}
website02_node = NodeMock(website02_data_dict)

website03_data_dict = {
    "labels": {'acme_Website'},
    "properties": {'from': 1566079200, 'name': 'website03'}
}
website03_node = NodeMock(website03_data_dict)

server02_data_dict = {
    "labels": {'acme_Server'},
    "properties": {'from': 1566079200, 'name': 'server02'}
}
server02_node = NodeMock(server02_data_dict)

rel_web1_ser2_data_dict = {
    "type": "DEPENDS_ON",
    "properties": {'periods': [1566165600, 1566252000, 1566338400]}
}
rel_web1_ser2_relationship = RelationshipMock(rel_web1_ser2_data_dict, website01_node, server02_node)

rel_web2_ser2_data_dict = {
    "type": "DEPENDS_ON",
    "properties": {'periods': [1566165600, 1566252000]}
}
rel_web2_ser2_relationship = RelationshipMock(rel_web2_ser2_data_dict, website02_node, server02_node)

rel_web3_ser2_data_dict = {
    "type": "DEPENDS_ON",
    "properties": {'periods': [1566338400]}
}
rel_web3_ser2_relationship = RelationshipMock(rel_web3_ser2_data_dict, website03_node, server02_node)

rel_off1_web1_data_dict = {
    "type": "DEPENDS_ON",
    "properties": {'periods': [1566338400]}
}
rel_off1_web1_relationship = RelationshipMock(rel_off1_web1_data_dict, offer01_node, website01_node)

rel_off1_web2_data_dict = {
    "type": "DEPENDS_ON",
    "properties": {'periods': [1566165600, 1566252000]}
}
rel_off1_web2_relationship = RelationshipMock(rel_off1_web2_data_dict, offer01_node, website02_node)

rel_off1_web3_data_dict = {
    "type": "DEPENDS_ON",
    "properties": {'periods': [1566165600, 1566252000, 1566338400]}
}
rel_off1_web3_relationship = RelationshipMock(rel_off1_web3_data_dict, offer01_node, website03_node)

impacted_node_multiple_paths_elements = [
    {
        "nodes": [offer01_node, website03_node, server02_node],
        "relationships": [rel_off1_web3_relationship, rel_web3_ser2_relationship]
    },
    {
        "nodes": [offer01_node, website01_node, server02_node],
        "relationships": [rel_off1_web1_relationship, rel_web1_ser2_relationship]
    },
    {
        "nodes": [offer01_node, website02_node, server02_node],
        "relationships": [rel_off1_web2_relationship, rel_web2_ser2_data_dict]
    }
]

impacted_node_data = {
    "impacted_node": offer01_node,
    "all_path_elements": impacted_node_multiple_paths_elements
}

impacted_websites_by_server02 = [
    {
        "impacted_node": website01_node,
        "all_path_elements": [
            {
                "nodes": [website01_node, server02_node],
                "relationships": [rel_web1_ser2_relationship]
            }
        ]
    },
    {
        "impacted_node": website02_node,
        "all_path_elements": [
            {
                "nodes": [website02_node, server02_node],
                "relationships": [rel_web2_ser2_relationship]
            }
        ]
    },
    {
        "impacted_node": website03_node,
        "all_path_elements": [
            {
                "nodes": [website03_node, server02_node],
                "relationships": [rel_web3_ser2_relationship]
            }
        ]
    }
]


def test_build_dependencies_query_without_config(app, create_team, create_rule, create_config):
    team_id = str(create_team('My team')['id'])

    with app.app_context():
        query = DependenciesController()._build_dependencies_query(
            team_id=team_id,
            topic='acme',
            label='Server',
            node='server.ovh.net',
            filter_on_config=False
        )
    assert query == ("MATCH(n:acme_Server{name: 'server.ovh.net'}) "
                     "OPTIONAL MATCH (n)-[r]->(m) "
                     "RETURN n,r,m ORDER BY m.name LIMIT 10")


def test_build_dependencies_query_rule(app, create_team, create_rule, create_config):
    team_id = str(create_team('My team')['id'])
    create_rule('Servers', team_id)
    create_config(team_id, {
        'Server': {'qos': 'rule.Servers'}
    })

    with app.app_context():
        query = DependenciesController()._build_dependencies_query(
            team_id=team_id,
            topic='acme',
            label='Server',
            node='server.ovh.net',
            filter_on_config=True
        )
    assert query == ("MATCH(n:acme_Server{name: 'server.ovh.net'}) "
                     "OPTIONAL MATCH (n)-[r]->(m) "
                     "RETURN n,r,m ORDER BY m.name LIMIT 10")


def test_build_dependencies_query_with_impacted_nodes(app, create_team, create_rule, create_config):
    team_id = str(create_team('My team')['id'])
    create_rule('Servers', team_id)
    create_config(team_id, {
        'Server': {'qos': 'rule.Servers'}
    })

    with app.app_context():
        query = DependenciesController()._build_dependencies_query(
            team_id=team_id,
            topic='acme',
            label='Server',
            node='server.ovh.net',
            filter_on_config=True,
            impacted=True
        )
    assert query == ("MATCH(n:acme_Server{name: 'server.ovh.net'}) "
                     "OPTIONAL MATCH (n)<-[r]-(m) "
                     "RETURN n,r,m ORDER BY m.name LIMIT 10")


@pytest.mark.parametrize("method", [("operation"), ("aggregation")])
def test_build_dependencies_query_one_dep(method, app, create_team, create_rule, create_config):
    team_id = str(create_team('My team')['id'])
    create_rule('Servers', team_id)
    create_config(team_id, {
        'Server': {'qos': 'rule.Servers'},
        'Cluster': {'qos': '{0}.AND[Server]'.format(method)}
    })

    with app.app_context():
        query = DependenciesController()._build_dependencies_query(
            team_id=team_id,
            topic='acme',
            label='Cluster',
            node='cluster.ovh.net',
            filter_on_config=True
        )
    assert query == ("MATCH(n:acme_Cluster{name: 'cluster.ovh.net'}) "
                     "OPTIONAL MATCH (n)-[r]->(m) "
                     "WHERE 'acme_Server' IN LABELS(m) "
                     "RETURN n,r,m ORDER BY m.name LIMIT 10")


@pytest.mark.parametrize("method", [("operation"), ("aggregation")])
def test_build_dependencies_query_multiple_deps(method, app, create_team, create_rule, create_config):
    team_id = str(create_team('My team')['id'])
    create_rule('Servers', team_id)
    create_config(team_id, {
        'ServerA': {'qos': 'rule.Servers'},
        'ServerB': {'qos': 'rule.Servers'},
        'Cluster': {'qos': '{0}.AND[ServerA, ServerB]'.format(method)}
    })

    with app.app_context():
        query = DependenciesController()._build_dependencies_query(
            team_id=team_id,
            topic='acme',
            label='Cluster',
            node='cluster.ovh.net',
            filter_on_config=True
        )
    assert query == ("MATCH(n:acme_Cluster{name: 'cluster.ovh.net'}) "
                     "OPTIONAL MATCH (n)-[r]->(m) "
                     "WHERE 'acme_ServerA' IN LABELS(m) "
                     "OR 'acme_ServerB' IN LABELS(m) "
                     "RETURN n,r,m ORDER BY m.name LIMIT 10")


def test_build_query_count_nodes(app):
    with app.app_context():
        query = DependenciesController()._build_query_count_nodes(
            topic='acme',
            labels=['Foo']
        )
    assert query == (
        "MATCH (n:acme_Foo) WITH 'Foo' AS Label, count(n) AS Count "
        "RETURN Label, Count "
    )

    with app.app_context():
        query = DependenciesController()._build_query_count_nodes(
            topic='acme',
            labels=['Foo', 'Bar', 'Baz']
        )
    assert query == (
        "MATCH (n:acme_Foo) WITH 'Foo' AS Label, count(n) AS Count "
        "RETURN Label, Count "
        "UNION MATCH (n:acme_Bar) WITH 'Bar' AS Label, count(n) AS Count "
        "RETURN Label, Count "
        "UNION MATCH (n:acme_Baz) WITH 'Baz' AS Label, count(n) AS Count "
        "RETURN Label, Count "
    )


def test_build_query_nodes(app):
    with app.app_context():
        query = DependenciesController()._build_query_nodes(
            topic='acme',
            label='Foo'
        )
    assert query == "MATCH (n:acme_Foo) WITH n RETURN n.name"

    with app.app_context():
        query = DependenciesController()._build_query_nodes(
            topic='acme',
            label='Foo',
            random=True
        )
    assert query == (
        "MATCH (n:acme_Foo) WITH n"
        ", rand() as r ORDER BY r "
        "RETURN n.name"
    )

    with app.app_context():
        query = DependenciesController()._build_query_nodes(
            topic='acme',
            label='Foo',
            random=True,
            name="bar"
        )
    assert query == (
        "MATCH (n:acme_Foo) WITH n"
        ", rand() as r ORDER BY r "
        "WHERE n.name CONTAINS 'bar' "
        "RETURN n.name"
    )

    with app.app_context():
        query = DependenciesController()._build_query_nodes(
            topic='acme',
            label='Foo',
            random=True,
            name="bar",
            limit=1234
        )
    assert query == (
        "MATCH (n:acme_Foo) WITH n"
        ", rand() as r ORDER BY r "
        "WHERE n.name CONTAINS 'bar' "
        "RETURN n.name "
        "LIMIT 1234"
    )


def test_build_impacted_nodes_queries(app):
    with app.app_context():
        query = DependenciesController()._build_impacted_nodes_queries(
            topic="acme", label="Server", node="server02", impacted_label="Website", skip=0, limit=25, count=False
        )
    assert query == "MATCH p = (n:acme_Website)-[*]->(:acme_Server{name: 'server02'}) " \
                    "WITH *, relationships(p) AS r_list WITH *, nodes(p) as n_sub_list RETURN DISTINCT n " \
                    "AS impacted_node, collect({ relationships: r_list, nodes: n_sub_list }) " \
                    "AS all_path_elements ORDER BY n.name SKIP 0 LIMIT 25"

    with app.app_context():
        query = DependenciesController()._build_impacted_nodes_queries(
            topic="acme", label="Server", node="server02", impacted_label="Website", count=True
        )
    assert query == "MATCH (n:acme_Website)-[*]->(:acme_Server{name: 'server02'}) " \
                    "RETURN count(DISTINCT n) AS count"


def test_are_path_elements_all_active(app):
    path_elements_mock_ko_invalid_node = {
        "nodes": [website01_node, server02_node],
        "relationships": [rel_web1_ser2_relationship]
    }

    path_elements_mock_ko_invalid_rel = {
        "nodes": [website02_node, server02_node],
        "relationships": [rel_web2_ser2_relationship]
    }

    path_elements_mock_ok = {
        "nodes": [website03_node, server02_node],
        "relationships": [rel_web3_ser2_relationship]
    }

    with app.app_context():
        bool_result = DependenciesController._are_path_elements_all_active(
            path_elements_mock_ko_invalid_node, 1566338400
        )
    assert bool_result is False

    with app.app_context():
        bool_result = DependenciesController._are_path_elements_all_active(
            path_elements_mock_ko_invalid_rel, 1566338400
        )
    assert bool_result is False

    with app.app_context():
        bool_result = DependenciesController._are_path_elements_all_active(
            path_elements_mock_ok, 1566338400
        )
    assert bool_result is True


def test_is_impacted_node_active(app):
    with app.app_context():
        bool_result = DependenciesController._is_impacted_node_active(impacted_node_data, 1566424800)
    assert bool_result is True

    with app.app_context():
        bool_result = DependenciesController._is_impacted_node_active(impacted_node_data, 1566252000)
    assert bool_result is False


def test_compute_impacted_nodes_from_data(app):
    with app.app_context():
        computed_impacted_nodes = DependenciesController._compute_impacted_nodes_from_data(
            impacted_websites_by_server02, 1566424800, True
        )
    assert computed_impacted_nodes == [
        {'active': True, 'name': 'website01', 'to': None, 'from': 1566424800},
        {'active': False, 'name': 'website02', 'to': None, 'from': 1566079200},
        {'active': True, 'name': 'website03', 'to': None, 'from': 1566079200}
    ]

    with app.app_context():
        computed_impacted_nodes = DependenciesController._compute_impacted_nodes_from_data(
            impacted_websites_by_server02, 1566338400, True
        )
    assert computed_impacted_nodes == [
        {'active': False, 'name': 'website01', 'to': None, 'from': 1566424800},
        {'active': False, 'name': 'website02', 'to': None, 'from': 1566079200},
        {'active': True, 'name': 'website03', 'to': None, 'from': 1566079200}
    ]

    with app.app_context():
        computed_impacted_nodes = DependenciesController._compute_impacted_nodes_from_data(
            impacted_websites_by_server02, 1566252000, True
        )
    assert computed_impacted_nodes == [
        {'active': False, 'name': 'website01', 'to': None, 'from': 1566424800},
        {'active': True, 'name': 'website02', 'to': None, 'from': 1566079200},
        {'active': False, 'name': 'website03', 'to': None, 'from': 1566079200}
    ]

    with app.app_context():
        computed_impacted_nodes = DependenciesController._compute_impacted_nodes_from_data(
            impacted_websites_by_server02, 1566079200, True
        )
    assert computed_impacted_nodes == [
        {'active': False, 'name': 'website01', 'to': None, 'from': 1566424800},
        {'active': False, 'name': 'website02', 'to': None, 'from': 1566079200},
        {'active': False, 'name': 'website03', 'to': None, 'from': 1566079200}
    ]

    with app.app_context():
        computed_impacted_nodes = DependenciesController._compute_impacted_nodes_from_data(
            impacted_websites_by_server02, 1566424800, False
        )
    assert computed_impacted_nodes == [
        {'active': True, 'name': 'website01', 'to': None, 'from': 1566424800},
        {'active': True, 'name': 'website03', 'to': None, 'from': 1566079200}
    ]
