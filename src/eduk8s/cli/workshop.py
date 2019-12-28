from __future__ import print_function

import yaml

import click
import requests

from kubernetes.client.rest import ApiException
from openshift.dynamic.exceptions import ResourceNotFoundError

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
        ctx.fail("The server doesn't have a resource type %s/%s." % (api_version, kind))


@root.group("workshop")
@click.pass_context
def group_workshop(ctx):
    """
    Manage workshop definitions.
    """

    pass


@group_workshop.command("import")
@click.pass_context
@click.argument("url", required=False)
@click.option(
    "-f", "--filename", default=None, help="File contains the workshop to import.",
)
def command_workshop_import(ctx, url, filename):
    """
    Import custom resource describing a workshop.
    """

    if filename:
        try:
            with open(filename) as fp:
                body = yaml.safe_load(fp)
        except Exception:
            raise
            ctx.fail("Failed to load workshop definition.")

    elif url:
        try:
            r = requests.get(url)
            body = yaml.safe_load(r.text)
        except Exception:
            ctx.fail("Failed to fetch workshop definition.")

    else:
        ctx.fail()

    client = kube.client()

    workshop_resource = _resource_type(
        ctx, client, "training.eduk8s.io/v1alpha1", "Workshop"
    )

    result = workshop_resource.create(body=body)

    click.echo("workshop.training.eduk8s.io/%s created" % result.metadata.name)


@group_workshop.command("enable")
@click.pass_context
@click.argument("name")
def command_workshop_enable(ctx, name):
    """
    Enable a workshop so that it can be deployed.
    """

    client = kube.client()

    workshop_resource = _resource_type(
        ctx, client, "training.eduk8s.io/v1alpha1", "Workshop"
    )

    workshop_body = {
        "kind": "Workshop",
        "apiVersion": "training.eduk8s.io/v1alpha1",
        "metadata": {"name": name},
        "status": {"enabled": True},
    }

    try:
        workshop_resource.patch(
            body=workshop_body, content_type="application/merge-patch+json"
        )
        click.echo("workshop.training.eduk8s.io/%s updated" % name)
    except ApiException as e:
        ctx.fail(e.reason)


@group_workshop.command("disable")
@click.pass_context
@click.argument("name")
def command_workshop_enable(ctx, name):
    """
    Disable a workshop so that it cannot be deployed.
    """

    client = kube.client()

    workshop_resource = _resource_type(
        ctx, client, "training.eduk8s.io/v1alpha1", "Workshop"
    )

    workshop_body = {
        "kind": "Workshop",
        "apiVersion": "training.eduk8s.io/v1alpha1",
        "metadata": {"name": name},
        "status": {"enabled": False},
    }

    try:
        workshop_resource.patch(
            body=workshop_body, content_type="application/merge-patch+json"
        )
        click.echo("workshop.training.eduk8s.io/%s updated" % name)
    except ApiException as e:
        ctx.fail(e.reason)


@group_workshop.command("remove")
@click.pass_context
@click.argument("name")
def command_workshop_remove(ctx, name):
    """
    Remove the custom resource describing a workshop.
    """

    client = kube.client()

    workshop_resource = _resource_type(
        ctx, client, "training.eduk8s.io/v1alpha1", "Workshop"
    )

    try:
        workshop_resource.delete(name=name)
        click.echo("workshop.training.eduk8s.io/%s deleted" % name)
    except ApiException as e:
        ctx.fail(e.reason)


@group_workshop.command("list")
@click.pass_context
def command_workshop_list(ctx):
    """
    List the set of imported workshop definitions.
    """

    client = kube.client()

    workshop_resource = _resource_type(
        ctx, client, "training.eduk8s.io/v1alpha1", "Workshop"
    )

    results = workshop_resource.get()

    cols = [["NAME", "IMAGE", "ENABLED"]]
    data = []

    for result in results.items:
        if result.status and result.status.enabled:
            enabled = "true"
        else:
            enabled = "false"

        data.append((result.metadata.name, result.spec.image, enabled))

    if data:
        click.echo("\n".join(_format_as_columns(cols, data)))
    else:
        click.echo("No workshops found.")
