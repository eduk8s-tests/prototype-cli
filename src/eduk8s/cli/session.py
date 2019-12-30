from __future__ import print_function

import random

import yaml

import click
import requests

from kubernetes.client.rest import ApiException
from openshift.dynamic.exceptions import ResourceNotFoundError
from openshift.dynamic import Resource, ResourceField, ResourceInstance

from ..cli import root
from .. import kube


def _format_as_columns(columns, data):
    data = columns + data

    widths = [max(map(len, col)) for col in zip(*data)]
    for row in data:
        yield "  ".join((val.ljust(width) for val, width in zip(row, widths)))


def _resource_type(ctx, client, api_version, kind):
    try:
        return client.resources.get(api_version=api_version, kind=kind)
    except ResourceNotFoundError:
        ctx.fail(f"The server doesn't have a resource type {api_version}/{kind}.")


@root.group("session")
@click.pass_context
def group_session(ctx):
    """
    Deploy workshops and manage sessions.
    """

    pass


@group_session.command("list")
@click.pass_context
def command_session_list(ctx):
    """
    List active workshop sessions.
    """

    client = kube.client()

    session_resource = _resource_type(
        ctx, client, "training.eduk8s.io/v1alpha1", "Session"
    )

    results = session_resource.get()

    cols = [["NAME", "IMAGE", "URL"]]
    data = []

    for result in results.items:
        data.append((result.metadata.name, result.spec.image, result.spec.url))

    if data:
        click.echo("\n".join(_format_as_columns(cols, data)))
    else:
        click.echo("No active workshop sessions found.")


_resource_budgets = {
    "small": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "small"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "1", "memory": "1Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "1", "memory": "1Gi"},
                        "default": {"cpu": "250m", "memory": "256Mi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "1Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "small"},
            },
            "spec": {
                "hard": {"limits.cpu": "1", "limits.memory": "1Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "small"},
            },
            "spec": {
                "hard": {"limits.cpu": "1", "limits.memory": "1Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "small"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "3",
                    "replicationcontrollers": "10",
                    "secrets": "20",
                    "services": "5",
                }
            },
        },
    },
    "medium": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "medium"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "2", "memory": "2Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "2", "memory": "2Gi"},
                        "default": {"cpu": "500m", "memory": "512Mi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "5Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "medium"},
            },
            "spec": {
                "hard": {"limits.cpu": "2", "limits.memory": "2Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "medium"},
            },
            "spec": {
                "hard": {"limits.cpu": "2", "limits.memory": "2Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "medium"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "6",
                    "replicationcontrollers": "15",
                    "secrets": "25",
                    "services": "10",
                }
            },
        },
    },
    "large": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "large"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "4", "memory": "4Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "4", "memory": "4Gi"},
                        "default": {"cpu": "500m", "memory": "1Gi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "10Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "large"},
            },
            "spec": {
                "hard": {"limits.cpu": "4", "limits.memory": "4Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "large"},
            },
            "spec": {
                "hard": {"limits.cpu": "4", "limits.memory": "4Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "large"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "12",
                    "replicationcontrollers": "25",
                    "secrets": "35",
                    "services": "20",
                }
            },
        },
    },
    "x-large": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "x-large"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "8", "memory": "8Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "8", "memory": "8Gi"},
                        "default": {"cpu": "500m", "memory": "2Gi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "20Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "x-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "8", "limits.memory": "8Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "x-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "8", "limits.memory": "8Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "x-large"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "18",
                    "replicationcontrollers": "35",
                    "secrets": "45",
                    "services": "30",
                }
            },
        },
    },
    "xx-large": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "xx-large"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "12", "memory": "12Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "12", "memory": "12Gi"},
                        "default": {"cpu": "500m", "memory": "2Gi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "20Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "xx-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "12", "limits.memory": "12Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "xx-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "12", "limits.memory": "12Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "xx-large"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "24",
                    "replicationcontrollers": "45",
                    "secrets": "55",
                    "services": "40",
                }
            },
        },
    },
    "xxx-large": {
        "resource-limits": {
            "kind": "LimitRange",
            "apiVersion": "v1",
            "metadata": {
                "name": "resource-limits",
                "annotations": {"resource-budget": "xxx-large"},
            },
            "spec": {
                "limits": [
                    {
                        "type": "Pod",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "16", "memory": "16Gi"},
                    },
                    {
                        "type": "Container",
                        "min": {"cpu": "50m", "memory": "32Mi"},
                        "max": {"cpu": "16", "memory": "16Gi"},
                        "default": {"cpu": "500m", "memory": "2Gi"},
                        "defaultRequest": {"cpu": "50m", "memory": "128Mi"},
                    },
                    {
                        "type": "PersistentVolumeClaim",
                        "min": {"storage": "1Gi"},
                        "max": {"storage": "20Gi"},
                    },
                ]
            },
        },
        "compute-resources": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources",
                "annotations": {"resource-budget": "xxx-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "16", "limits.memory": "16Gi"},
                "scopes": ["NotTerminating"],
            },
        },
        "compute-resources-timebound": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "compute-resources-timebound",
                "annotations": {"resource-budget": "xxx-large"},
            },
            "spec": {
                "hard": {"limits.cpu": "16", "limits.memory": "16Gi"},
                "scopes": ["Terminating"],
            },
        },
        "object-counts": {
            "kind": "ResourceQuota",
            "apiVersion": "v1",
            "metadata": {
                "name": "object-counts",
                "annotations": {"resource-budget": "xxx-large"},
            },
            "spec": {
                "hard": {
                    "persistentvolumeclaims": "30",
                    "replicationcontrollers": "55",
                    "secrets": "65",
                    "services": "50",
                }
            },
        },
    },
}


def _setup_limits_and_quotas(
    ctx, client, spawner_namespace, target_namespace, service_account, role, budget
):
    limit_range_resource = _resource_type(ctx, client, "v1", "LimitRange")
    resource_quota_resource = _resource_type(ctx, client, "v1", "ResourceQuota")
    role_binding_resource = _resource_type(
        ctx, client, "rbac.authorization.k8s.io/v1", "RoleBinding"
    )

    # Create role binding in the project so the users service account
    # can create resources in it.

    role_binding_body = {
        "apiVersion": "rbac.authorization.k8s.io/v1",
        "kind": "RoleBinding",
        "metadata": {"name": "eduk8s"},
        "roleRef": {
            "apiGroup": "rbac.authorization.k8s.io",
            "kind": "ClusterRole",
            "name": f"{role}",
        },
        "subjects": [
            {
                "kind": "ServiceAccount",
                "name": f"{service_account}",
                "namespace": f"{spawner_namespace}",
            }
        ],
    }

    role_binding_resource.create(namespace=target_namespace, body=role_binding_body)

    # Determine what project namespace resources need to be used.

    if budget != "unlimited":
        if budget not in _resource_budgets:
            budget = "default"
        elif not _resource_budgets[budget]:
            budget = "default"

    if budget not in ("default", "unlimited"):
        budget_item = _resource_budgets[budget]

        resource_limits_definition = budget_item["resource-limits"]
        compute_resources_definition = budget_item["compute-resources"]
        compute_resources_timebound_definition = budget_item[
            "compute-resources-timebound"
        ]
        object_counts_definition = budget_item["object-counts"]

    # Delete any limit ranges applied to the project that may conflict
    # with the limit range being applied. For the case of unlimited, we
    # delete any being applied but don't replace it.

    if budget != "default":
        limit_ranges = limit_range_resource.get(namespace=target_namespace)

        for limit_range in limit_ranges.items:
            limit_range_resource.delete(
                namespace=target_namespace, name=limit_range.metadata.name
            )

    # Create limit ranges for the project namespace so any deployments
    # will have default memory/cpu min and max values.

    if budget not in ("default", "unlimited"):
        resource_limits_body = resource_limits_definition
        limit_range_resource.create(
            namespace=target_namespace, body=resource_limits_body
        )

    # Delete any resource quotas applied to the project namespace that
    # may conflict with the resource quotas being applied.

    if budget != "default":
        resource_quotas = resource_quota_resource.get(namespace=target_namespace)

        for resource_quota in resource_quotas.items:
            resource_quota_resource.delete(
                namespace=target_namespace, name=resource_quota.metadata.name
            )

    # Create resource quotas for the project so there is a maximum for
    # what resources can be used.

    if budget not in ("default", "unlimited"):
        resource_quota_body = compute_resources_definition
        resource_quota_resource.create(
            namespace=target_namespace, body=resource_quota_body
        )

        resource_quota_body = compute_resources_timebound_definition
        resource_quota_resource.create(
            namespace=target_namespace, body=resource_quota_body
        )

        resource_quota_body = object_counts_definition
        resource_quota_resource.create(
            namespace=target_namespace, body=resource_quota_body
        )


@group_session.command("deploy")
@click.pass_context
@click.argument("name", required=False)
def command_session_deploy(ctx, name):
    """
    Deploy an instance of a workshop.
    """

    # Setup Kubernetes client and make sure custom resources defined.

    client = kube.client()

    deployment_resource = _resource_type(ctx, client, "apps/v1", "Deployment")
    namespace_resource = _resource_type(ctx, client, "v1", "Namespace")
    secret_resource = _resource_type(ctx, client, "v1", "Secret")
    service_resource = _resource_type(ctx, client, "v1", "Service")
    service_account_resource = _resource_type(ctx, client, "v1", "ServiceAccount")

    session_resource = _resource_type(
        ctx, client, "training.eduk8s.io/v1alpha1", "Session"
    )
    workshop_resource = _resource_type(
        ctx, client, "training.eduk8s.io/v1alpha1", "Workshop"
    )

    # Verify workshop definition exists and is enabled for use.

    try:
        workshop_instance = workshop_resource.get(name=name)
    except ApiException as e:
        if e.status == 404:
            ctx.fail(f"Workshop with name '{name}' does not exist.")
        raise

    if not workshop_instance.status or not workshop_instance.status.enabled:
        ctx.fail(f"Workshop with name '{name}' is not enabled.")

    # Create session object to act as owner for workshop resources
    # and create the corresponding namespace as well.

    spawner_namespace = name

    random_userid_chars = "bcdfghjklmnpqrstvwxyz0123456789"

    def _generate_random_userid(n=5):
        return "".join(random.choice(random_userid_chars) for _ in range(n))

    count = 0

    while True:
        count += 1

        session_id = _generate_random_userid()
        session_name = f"{name}-{session_id}"

        session_body = {
            "apiVersion": "training.eduk8s.io/v1alpha1",
            "kind": "Session",
            "metadata": {
                "name": f"{session_name}",
                "ownerReferences": [
                    {
                        "apiVersion": "training.eduk8s.io/v1alpha1",
                        "kind": "Workshop",
                        "blockOwnerDeletion": True,
                        "controller": True,
                        "name": f"{workshop_instance.metadata.name}",
                        "uid": f"{workshop_instance.metadata.uid}",
                    }
                ],
            },
            "spec": {
                "vendor": f"{workshop_instance.spec.vendor}",
                "name": f"{name}",
                "title": f"{workshop_instance.spec.title}",
                "description": f"{workshop_instance.spec.description}",
                "url": f"{workshop_instance.spec.url}",
                "image": f"{workshop_instance.spec.image}",
                "budget": f"{workshop_instance.spec.budget or 'default'}",
                "duration": f"{workshop_instance.spec.timeout or '0'}",
                "timeout": f"{workshop_instance.spec.timeout or '0'}",
            },
        }

        try:
            session_instance = session_resource.create(body=session_body)
        except ApiException as e:
            if e.status == 409:
                if count > 10:
                    ctx.fail(f"Failed to create session for workshop '{name}'.")
                continue
            else:
                raise

        project_namespace = session_name

        namespace_body = {
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {
                "name": f"{project_namespace}",
                "ownerReferences": [
                    {
                        "apiVersion": "training.eduk8s.io/v1alpha1",
                        "kind": "Session",
                        "blockOwnerDeletion": True,
                        "controller": True,
                        "name": f"{session_instance.metadata.name}",
                        "uid": f"{session_instance.metadata.uid}",
                    }
                ],
            },
        }

        try:
            namespace_instance = namespace_resource.create(body=namespace_body)
        except ApiException as e:
            if e.status == 409:
                session_resource.delete(body=session_body)
                continue
            else:
                raise

        break

    # Create service account under which the workshop runs.

    service_account = f"user-{session_id}"

    service_account_body = {
        "apiVersion": "v1",
        "kind": "ServiceAccount",
        "metadata": {
            "name": f"{service_account}",
            "ownerReferences": [
                {
                    "apiVersion": "training.eduk8s.io/v1alpha1",
                    "kind": "Session",
                    "blockOwnerDeletion": True,
                    "controller": True,
                    "name": f"{session_instance.metadata.name}",
                    "uid": f"{session_instance.metadata.uid}",
                }
            ],
        },
    }

    service_account_resource.create(
        namespace=spawner_namespace, body=service_account_body
    )

    # Setup project namespace limit ranges and resource quotas.

    default_role = workshop_instance.spec.role or "admin"
    default_budget = workshop_instance.spec.budget or "default"

    _setup_limits_and_quotas(
        ctx,
        client,
        spawner_namespace,
        project_namespace,
        service_account,
        default_role,
        default_budget,
    )

    # Create the additional resources required for the workshop.

    def _namespaced_resources():
        api_groups = client.resources.parse_api_groups()

        for api in api_groups.values():
            for domain, items in api.items():
                for version, group in items.items():
                    try:
                        for kind in group.resources:
                            if domain:
                                version = f"{domain}/{version}"
                            resource = client.resources.get(
                                api_version=version, kind=kind
                            )
                            if type(resource) == Resource and resource.namespaced:
                                yield (version, resource.kind)
                    except Exception:
                        pass

    namespaced_resources = set(_namespaced_resources())

    for body in workshop_instance.spec.resources:
        kind = body.kind
        api_version = body.apiVersion

        if not (api_version, kind) in namespaced_resources:
            body.metadata.ownerReferences = [
                dict(
                    apiVersion="training.eduk8s.io/v1alpha1",
                    kind="Session",
                    blockOwnerDeletion=True,
                    controller=True,
                    name=session_instance.metadata.name,
                    uid=session_instance.metadata.uid,
                )
            ]

        body = ResourceInstance(client, body).to_dict()

        def _substitute_variables(obj):
            if isinstance(obj, str):
                obj = obj.replace("$(spawner_namespace)", spawner_namespace)
                obj = obj.replace("$(project_namespace)", project_namespace)
                obj = obj.replace("$(service_account)", service_account)
                return obj
            elif isinstance(obj, dict):
                return {k: _substitute_variables(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_substitute_variables(v) for v in obj]
            else:
                return obj

        body = _substitute_variables(body)

        resource = client.resources.get(api_version=api_version, kind=kind)

        target_namespace = body["metadata"].get("namespace", project_namespace)

        resource.create(namespace=target_namespace, body=body)

        if kind.lower() == "namespace":
            annotations = body["metadata"].get("annotations", {})

            role = annotations.get("session/role", default_role)
            budget = annotations.get("session/budget", default_budget)

            namespace = body["metadata"]["name"]

            _setup_limits_and_quotas(
                ctx, client, spawner_namespace, namespace, service_account, role, budget
            )

    # Deploy the actual workshop dashboard for the workshop.

    secret_body = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": "kubernetes-dashboard-csrf"},
    }

    secret_resource.create(namespace=project_namespace, body=secret_body)

    deployment_body = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": f"workshop-{session_id}",
            "ownerReferences": [
                {
                    "apiVersion": "training.eduk8s.io/v1alpha1",
                    "kind": "Session",
                    "blockOwnerDeletion": True,
                    "controller": True,
                    "name": f"{session_instance.metadata.name}",
                    "uid": f"{session_instance.metadata.uid}",
                }
            ],
        },
        "spec": {
            "replicas": 1,
            "selector": {"matchLabels": {"deployment": "workshop"}},
            "strategy": {"type": "Recreate"},
            "template": {
                "metadata": {"labels": {"deployment": "workshop"}},
                "spec": {
                    "serviceAccountName": f"{service_account}",
                    "containers": [
                        {
                            "name": "dashboard",
                            "image": f"{workshop_instance.spec.image}",
                            "imagePullPolicy": "Always",
                            "ports": [{"containerPort": 10080, "protocol": "TCP"}],
                            "env": [
                                {
                                    "name": "PROJECT_NAMESPACE",
                                    "value": f"{project_namespace}",
                                }
                            ],
                        }
                    ],
                },
            },
        },
    }

    deployment_resource.create(namespace=spawner_namespace, body=deployment_body)

    service_body = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"workshop-{session_id}",
            "ownerReferences": [
                {
                    "apiVersion": "training.eduk8s.io/v1alpha1",
                    "kind": "Session",
                    "blockOwnerDeletion": True,
                    "controller": True,
                    "name": f"{session_instance.metadata.name}",
                    "uid": f"{session_instance.metadata.uid}",
                }
            ],
        },
        "spec": {
            "type": "ClusterIP",
            "ports": [{"port": 10080, "protocol": "TCP", "targetPort": 10080}],
            "selector": {"deployment": "workshop"},
        },
    }

    service_resource.create(namespace=spawner_namespace, body=service_body)

    click.echo(f"session.training.eduk8s.io/{session_name} created")


@group_session.command("delete")
@click.pass_context
@click.argument("name", required=False)
def command_session_deploy(ctx, name):
    """
    Delete an instance of a workshop.
    """

    client = kube.client()

    session_resource = _resource_type(
        ctx, client, "training.eduk8s.io/v1alpha1", "Session"
    )

    try:
        session_resource.delete(name=name)
        click.echo(f"session.training.eduk8s.io/{name} deleted")
    except ApiException as e:
        ctx.fail(e.reason)
