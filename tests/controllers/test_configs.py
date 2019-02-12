import pytest


def test_create_context_from_config():
    from depc.apiv1.configs import ConfigController

    config = {'Offer': {'qos': 'aggregation.AVERAGE[Website]'}, 'Filer': {'qos': 'rule.Servers'},
              'Website': {'qos': 'operation.AND[Filer, Apache]'}, 'Apache': {'qos': 'rule.Servers'}}

    config_context = ConfigController()._create_context_from_config(config)

    assert config_context == {
        'labels_with_downstream': {'Website': ('Offer', 'aggregation'), 'Filer': ('Website', 'operation'),
                                   'Apache': ('Website', 'operation')},
        'all_labels': {'Website': {'dependencies': ['Filer', 'Apache'], 'compute_type': 'operation'},
                       'Filer': {'rule_name': 'Servers', 'compute_type': 'rule'},
                       'Offer': {'dependencies': ['Website'], 'compute_type': 'aggregation'},
                       'Apache': {'rule_name': 'Servers', 'compute_type': 'rule'}}}


def test_create_context_from_config_only_one_rule():
    from depc.apiv1.configs import ConfigController

    config = {'Apache': {'qos': 'rule.Servers'}}

    config_context = ConfigController()._create_context_from_config(config)

    assert config_context == {
        'labels_with_downstream': {},
        'all_labels': {'Apache': {'rule_name': 'Servers', 'compute_type': 'rule'}}}


def test_check_config_from_context(app, create_team, create_rule):
    from depc.apiv1.configs import ConfigController

    team_id = '533cbab1-f824-4160-beab-b54f3ea52335'
    create_team(team_id)
    create_rule('Servers', team_id)

    config_context = {'labels_with_downstream': {'Website': ('Offer', 'aggregation'), 'Filer': ('Website', 'operation'),
                                                 'Apache': ('Website', 'operation')},
                      'all_labels': {'Website': {'dependencies': ['Filer', 'Apache'], 'compute_type': 'operation'},
                                     'Filer': {'rule_name': 'Servers', 'compute_type': 'rule'},
                                     'Offer': {'dependencies': ['Website'], 'compute_type': 'aggregation'},
                                     'Apache': {'rule_name': 'Servers', 'compute_type': 'rule'}}}

    with app.app_context():
        ConfigController()._check_config_from_context(config_context, team_id)


def test_check_config_from_context_only_one_rule(app, create_team, create_rule):
    from depc.apiv1.configs import ConfigController

    team_id = '533cbab1-f824-4160-beab-b54f3ea52335'
    create_team(team_id)
    create_rule('Servers', team_id)

    config_context = {'labels_with_downstream': {},
                      'all_labels': {'Apache': {'rule_name': 'Servers', 'compute_type': 'rule'}}}

    with app.app_context():
        ConfigController()._check_config_from_context(config_context, team_id)


def test_check_config_from_context_integrity_error(app, create_team, create_rule):
    from depc.apiv1.configs import ConfigController
    from depc.controllers import IntegrityError

    team_id = '533cbab1-f824-4160-beab-b54f3ea52335'
    create_team(team_id)
    create_rule('Servers', team_id)

    config_context = {'labels_with_downstream': {'Website': ('Offer', 'aggregation'), 'Filer': ('Website', 'operation'),
                                                 'Apache': ('Website', 'operation'), 'Offer': ('Wrong', 'operation')},
                      'all_labels': {'Website': {'dependencies': ['Filer', 'Apache'], 'compute_type': 'operation'},
                                     'Filer': {'rule_name': 'Servers', 'compute_type': 'rule'},
                                     'Offer': {'dependencies': ['Website'], 'compute_type': 'aggregation'},
                                     'Apache': {'rule_name': 'Servers', 'compute_type': 'rule'},
                                     'Wrong': {'dependencies': ['Offer'], 'compute_type': 'operation'}}}

    with app.app_context():
        with pytest.raises(IntegrityError) as err:
            ConfigController()._check_config_from_context(config_context, team_id)
        assert err.value.message == 'Label "Wrong" could not be executed after label "Offer"'


def test_check_config_from_context_rule_not_found_error(app, create_team, create_rule):
    from depc.apiv1.configs import ConfigController
    from depc.controllers import NotFoundError

    team_id = '533cbab1-f824-4160-beab-b54f3ea52335'
    create_team(team_id)
    create_rule('Servers', team_id)

    config_context = {'labels_with_downstream': {'Website': ('Offer', 'aggregation'), 'Filer': ('Website', 'operation'),
                                                 'Apache': ('Website', 'operation')},
                      'all_labels': {'Website': {'dependencies': ['Filer', 'Apache'], 'compute_type': 'operation'},
                                     'Filer': {'rule_name': 'Servers', 'compute_type': 'rule'},
                                     'Offer': {'dependencies': ['Website'], 'compute_type': 'aggregation'},
                                     'Apache': {'rule_name': 'RuleDoesNotExist', 'compute_type': 'rule'}}}

    with app.app_context():
        with pytest.raises(NotFoundError) as err:
            ConfigController()._check_config_from_context(config_context, team_id)
        assert err.value.message == 'Rule "RuleDoesNotExist" defined in label "Apache" does not exist'


def test_check_config_from_context_only_one_rule_not_found_error(app, create_team, create_rule):
    from depc.apiv1.configs import ConfigController
    from depc.controllers import NotFoundError

    team_id = '533cbab1-f824-4160-beab-b54f3ea52335'
    create_team(team_id)
    create_rule('Servers', team_id)

    config_context = {'labels_with_downstream': {},
                      'all_labels': {'Apache': {'rule_name': 'RuleDoesNotExist', 'compute_type': 'rule'}}}

    with app.app_context():
        with pytest.raises(NotFoundError) as err:
            ConfigController()._check_config_from_context(config_context, team_id)
        assert err.value.message == 'Rule "RuleDoesNotExist" defined in label "Apache" does not exist'


def test_check_config_from_context_dependencie_not_declared(app, create_team, create_rule):
    from depc.apiv1.configs import ConfigController
    from depc.controllers import NotFoundError

    team_id = '533cbab1-f824-4160-beab-b54f3ea52335'
    create_team(team_id)
    create_rule('Servers', team_id)

    config_context = {
        'labels_with_downstream': {'Website': ('Offer', 'aggregation'), 'Filer': ('Website', 'operation')},
        'all_labels': {'Website': {'dependencies': ['Filer', 'Apache'], 'compute_type': 'operation'},
                       'Filer': {'rule_name': 'Servers', 'compute_type': 'rule'},
                       'Offer': {'dependencies': ['Website'], 'compute_type': 'aggregation'}
                       }}

    with app.app_context():
        with pytest.raises(NotFoundError) as err:
            ConfigController()._check_config_from_context(config_context, team_id)
        assert err.value.message == 'Dependency "Apache" declared in label "Website" ' \
                                    'has not been declared in the configuration'
