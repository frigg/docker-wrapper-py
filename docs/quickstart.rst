Quickstart
----------

Install
~~~~~~~

Install docker-wrapper with pip:

::

    pip install docker-wrapper

Usage
~~~~~

.. code-block:: python

    with Docker() as docker:
        docker.run('command')
