Quickstart
----------

Install
~~~~~~~

Install docker-wrapper with pip:

::

    pip install docker-wrapper

Usage
~~~~~

Use it in a with statement:

.. code-block:: python

    with Docker() as docker:
        docker.run('command')

or as a decorator:
.. code-block:: python

    @Docker.wrap()
    def run_command_in_container(command, docker)
        docker.run(command)
