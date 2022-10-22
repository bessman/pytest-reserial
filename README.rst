===============
pytest-reserial
===============

.. image:: https://img.shields.io/pypi/v/pytest-reserial.svg
    :target: https://pypi.org/project/pytest-reserial
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/pytest-reserial.svg
    :target: https://pypi.org/project/pytest-reserial
    :alt: Python versions

.. image:: https://ci.appveyor.com/api/projects/status/github/bessman/pytest-reserial?branch=master
    :target: https://ci.appveyor.com/project/bessman/pytest-reserial/branch/master
    :alt: See Build Status on AppVeyor

Record and replay serial port traffic with pytest.

Features
--------

pytest-reserial adds a pytest fixture, 'reserial'. With this fixture, tests which
communicate with external devices over a serial port can record any traffic generated
during the test. After serial traffic for a certain test has been recorded, that traffic
can be replayed when said test is running, eliminating the need for the external devices
to be connected.

Recording
---------

To record serial port traffic, call pytest with the '--record' option::

    $ pytest --record

Traffic recordings are stored as JSON files. One file is created for each test. The log
files are stored in a directory structure which matches the layout of the test files,
like so::

    test_one.py
        def test_a_thing():
            ...
        def test_other_thing():
            ...
    test_two.py
        def test_third_thing()
            ...

Results in::

    <logdir>/
        test_one/
            test_a_thing.json
            test_other_thing.json
        test_two/
            test_third_thing.json

Where <logdir> defaults to <testdir>/traffic_logs, where <testdir> is the location of
the test scripts. The base directory for storing log files can be changed with the
'--logdir' option::

    $ pytest --record --logdir=mylogdir

Result::

    mylogdir/
        test_one/
            test_a_thing.json
            test_other_thing.json
        test_two/
            test_third_thing.json

Replaying
---------
To replay recorded serial traffic, simply pass the '--replay' option::

    $ pytest --replay

If the log directory is not the default (<testdir>/traffic_logs), you must also pass
the location of the recordings with the '--logdir' option::

    $ pytest --replay --logdir=mylogdir

Requirements
------------

'reserial' depends on 'pyserial'.


Installation
------------

You can install "pytest-reserial" via `pip`_ from `PyPI`_::

    $ pip install pytest-reserial


Usage
-----

* TODO

Contributing
------------
Contributions are very welcome. Tests can be run with `tox`_, please ensure
the coverage at least stays the same before you submit a pull request.

License
-------

Distributed under the terms of the `MIT`_ license, "pytest-reserial" is free and open source software.


Issues
------

If you encounter any problems, please `file an issue`_ along with a detailed description.

.. _`Cookiecutter`: https://github.com/audreyr/cookiecutter
.. _`@hackebrot`: https://github.com/hackebrot
.. _`MIT`: http://opensource.org/licenses/MIT
.. _`BSD-3`: http://opensource.org/licenses/BSD-3-Clause
.. _`GNU GPL v3.0`: http://www.gnu.org/licenses/gpl-3.0.txt
.. _`Apache Software License 2.0`: http://www.apache.org/licenses/LICENSE-2.0
.. _`cookiecutter-pytest-plugin`: https://github.com/pytest-dev/cookiecutter-pytest-plugin
.. _`file an issue`: https://github.com/bessman/pytest-reserial/issues
.. _`pytest`: https://github.com/pytest-dev/pytest
.. _`tox`: https://tox.readthedocs.io/en/latest/
.. _`pip`: https://pypi.org/project/pip/
.. _`PyPI`: https://pypi.org/project

----

This `pytest`_ plugin was generated with `Cookiecutter`_ along with `@hackebrot`_'s `cookiecutter-pytest-plugin`_ template.
