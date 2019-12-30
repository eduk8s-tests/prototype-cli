import click

from ..cli import root


@root.group("install")
@click.pass_context
def group_install(ctx):
    """
    Install workshop components.
    """

    pass


@group_install.command("crds")
@click.pass_context
def command_install_crds(ctx):
    """
    Install required custom resource definitions.
    """

    pass


@group_install.command("operator")
@click.pass_context
def command_install_operator(ctx):
    """
    Install operator for managing workhops.
    """

    pass
