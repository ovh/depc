import arrow
from flask import abort, jsonify, request
from flask_login import login_required

from depc.apiv1 import api
from depc.controllers.dependencies import DependenciesController
from depc.users import TeamPermission


@api.route("/teams/<team_id>/labels")
@login_required
def get_labels(team_id):
    """Get the labels of a team.

    .. :quickref: GET; Get the labels of a team.

    **Example request**:

    .. sourcecode:: http

      GET /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/labels HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      [
        {
          "name": "Filer",
          "nodes_count": 2,
          "qos_query": "rule.Servers"
        },
        {
          "name": "Website",
          "nodes_count": 2,
          "qos_query": "operation.AND[Filer, Apache]"
        },
        {
          "name": "Apache",
          "nodes_count": 2,
          "qos_query": "rule.Servers"
        },
        {
          "name": "Offer",
          "nodes_count": 1,
          "qos_query": "aggregation.AVERAGE[Website]"
        }
      ]

    :resheader Content-Type: application/json
    :status 200: the list of labels
    """
    if not TeamPermission.is_user(team_id):
        abort(403)

    return jsonify(DependenciesController.get_labels(team_id))


@api.route("/teams/<team_id>/labels/<label>/nodes")
@login_required
def get_label_nodes(team_id, label):
    """Get the nodes of a label.

    .. :quickref: GET; Get the nodes of a label.

    **Example request**:

    .. sourcecode:: http

      GET /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/labels/Website/nodes HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      [
        "example-one.com",
        "example-two.com"
      ]

    :param name: Filter the list by name
    :param limit: Limit the number of results
    :param random: Return random items
    :resheader Content-Type: application/json
    :status 200: the list of nodes
    """
    if not TeamPermission.is_user(team_id):
        abort(403)

    return jsonify(
        DependenciesController.get_label_nodes(
            team_id,
            label,
            request.args.get("name", None),
            request.args.get("limit", None),
            request.args.get("random", False),
        )
    )


@api.route("/teams/<team_id>/labels/<label>/nodes/<path:node>/count")
@login_required
def count_node_dependencies(team_id, label, node):
    """Count the dependencies of a node.

    .. :quickref: GET; Count the dependencies of a node.

    **Example request**:

    .. sourcecode:: http

      GET /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/labels/MyLabel/nodes/mynode/count HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        'count': 10
      }

    :resheader Content-Type: application/json
    :status 200: the number of dependencies
    """
    if not TeamPermission.is_user(team_id):
        abort(403)

    return jsonify(DependenciesController.count_node_dependencies(team_id, label, node))


@api.route("/teams/<team_id>/labels/<label>/nodes/<path:node>")
@login_required
def get_node(team_id, label, node):
    """Get the dependencies of a node.

    .. :quickref: GET; Get the dependencies of a node.

    **Example request**:

    .. sourcecode:: http

      GET /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/labels/Website/nodes/example.com HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {
        "dependencies": {
          "Apache": [{
            "name": "apache1",
            "old": false,
            "periods": [0]
          }],
          "Filer": [{
            "name": "filer1",
            "old": false,
            "periods": [0]
          }],
          "Website": [{
              "name": "example.com"
           }]
        },
        "graph": {
          "nodes": [{
            "id": 8226314,
            "label": "example.com",
            "title": "Website"
          }, {
            "id": 8226318,
            "label": "apache1",
            "title": "Apache"
          }, {
            "id": 8226316,
            "label": "filer1",
            "title": "Filer"
          }],
          "relationships": [{
            "arrows": "to",
            "from": 8226314,
            "id": 13558159,
            "periods": [0],
            "to": 8226318
          }, {
            "arrows": "to",
            "from": 8226314,
            "id": 13558157,
            "periods": [0],
            "to": 8226316
          }]
        },
        "name": "example.com"
      }

    :param alone: Returns the node without its dependencies
    :param day: Filter by day (default is today)
    :param config: Only include labels used in configuration
    :param inactive: Include the inactive nodes
    :param impacted: Display the impacted nodes
    :resheader Content-Type: application/json
    :status 200: the list of dependencies
    """
    if not TeamPermission.is_user(team_id):
        abort(403)

    # We just want to return the node
    data = DependenciesController.get_label_node(team_id, label, node)
    if request.args.get("alone", False):
        return jsonify(data)

    # We also want the dependencies
    data.update(
        DependenciesController.get_node_dependencies(
            team_id=team_id,
            label=label,
            node=node,
            day=request.args.get("day", arrow.utcnow().format("YYYY-MM-DD")),
            filter_on_config=request.args.get("config", False),
            include_inactive=request.args.get("inactive", False),
            display_impacted=request.args.get("impacted", False),
        )
    )
    return jsonify(data)


@api.route("/teams/<team_id>/labels/<label>/nodes/<path:node>", methods=["DELETE"])
@login_required
def delete_node(team_id, label, node):
    """Delete a node.

    .. :quickref: DELETE; Delete a node.

    **Example request**:

    .. sourcecode:: http

      DELETE /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/labels/Website/nodes/example.com HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      {}

    :resheader Content-Type: application/json
    :param detach: Remove the relations of the node
    :status 200: the node has been deleted
    """
    if not TeamPermission.is_manager(team_id):
        abort(403)

    return jsonify(
        DependenciesController.delete_node(
            team_id=team_id,
            label=label,
            node=node,
            detach=request.args.get("detach", False),
        )
    )


@api.route("/teams/<team_id>/labels/<label>/nodes/<path:node>/impacted-nodes")
@login_required
def get_impacted_nodes(team_id, label, node):
    """Get the nodes impacted by a given node.

    .. :quickref: GET; Get the nodes impacted by a given node.

    **Example request**:

    .. sourcecode:: http

      GET /v1/teams/66859c4a-3e0a-4968-a5a4-4c3b8662acb7/labels/Website/nodes/example.com?impactedLabel=Offer HTTP/1.1
      Host: example.com
      Accept: application/json

    **Example response**:

    .. sourcecode:: http

      HTTP/1.1 200 OK

      [
        "premium"
      ]

    :param impactedLabel: impacted nodes for the given label
    :resheader Content-Type: application/json
    :status 200: the array of impacted nodes
    """

    if not TeamPermission.is_user(team_id):
        abort(403)

    return jsonify(
        DependenciesController.get_impacted_nodes(
            team_id, label, node, request.args.get("impactedLabel", None)
        )
    )
