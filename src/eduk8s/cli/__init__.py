import click

ENTRYPOINTS = "eduk8s_cli_plugins"


@click.group()
@click.pass_context
def root(ctx):
    """
    Command line client for eduk8s.

    For more details see:

        https://github.com/eduk8s/eduk8s-cli

    """


def main():
    # Import any plugins for extending the available commands. They
    # should automatically register themselves against the appropriate
    # CLI command group.

    try:
        import pkg_resources
    except ImportError:
        pass
    else:
        entrypoints = pkg_resources.iter_entry_points(group=ENTRYPOINTS)

        for entrypoint in entrypoints:
            __import__(entrypoint.module_name)

    # Call the CLI to process the command line arguments and execute
    # the appropriate action.

    root(obj={})


if __name__ == "__main__":
    main()
