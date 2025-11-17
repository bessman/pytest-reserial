# pytest-reserial

![build](https://github.com/bessman/pytest-reserial/actions/workflows/main.yml/badge.svg?branch=main)
[![PyPI](https://img.shields.io/pypi/v/pytest-reserial.svg)](https://pypi.org/project/pytest-reserial/)
[![License](https://img.shields.io/pypi/l/pytest-reserial)](https://mit-license.org/)

Pytest plugin for recording and replaying serial port traffic during tests.

## Installation

`pip install pytest-reserial`

## Usage

1.  Write your tests as if they would run with the device connected. While you iterate you can use `pytest --disable-reserial` to have your code interact with the device without any side effects.

2.  When your tests pass with the device connected, run `pytest --record` to record serial traffic 
    from the passing tests.

3.  Now you can disconnect the device and run your tests with `pytest`.

A simple example:

```python
# my_serial_app.py
from serial import Serial

def my_serial_app():
    with Serial(port=/dev/ttyUSB0) as s:
        # When we send '1' to the device, it responds with '2'.
        s.write(b"\x01")
        return s.read()

# Just use the 'reserial' fixture!
def test_my_serial_app(reserial):
    assert my_serial_app() == b"\x02"
```

Next:

1.  Connect the device.
2.  Run `pytest my_serial_app.py --disable-reserial` and verify that the test passes with the device connected.
3.  Run `pytest --record my_serial_app.py`. The test will run again, and the traffic will be recorded.
4.  Disconnect the device.
5.  Run `pytest my_serial_app.py`. The test will pass!

The logged traffic will be stored as JSON Lines, with one file per test file and one line per test, in the same directory as your test files. The files will have the same names as the test files except with a .jsonl extension instead of .py. For example, if your project layout is:

```shell
├── src
│   ├── myproject
│   │   ├── ...
├── tests
│   ├── test_myproject.py
```

Then after running `pytest --record`, the tests/ directory will contain a new file, test_myproject.jsonl, containing the recorded serial traffic from the tests.

## Why

Have you ever tried to write tests for a program that talks to an external device over serial (like an Arduino or something)? You probably wrote the tests assuming that the device is question would always be connected when running the tests, right? And later you got bit by one or more of the pitfalls of that approach:

-   You wanted to run the tests when the device wasn't connected. Perhaps you were travelling, or
    someone had borrowed it. Whatever the reason, you found yourself unable to run the tests, and
    therefore unable to continue development, until you could connect the device again.

-   You made a change to your program, and one of your tests failed. So far so good, right? That's
    what tests are for, after all. Only, you can't figure out why the test is failing. You spend
    several hours trying to fix it, but eventually give up and revert your changes.
    But the test still fails.
    So you try another device, and sure enough, now it passes. Turns out, what you thought was a
    problem with your code was actually a hardware failure.

-   Some of the tests depend on the device being in a certain state, and some of the tests depend on
    the device being in *another* state. So you can't run the entire test suite all at once, instead
    being forced to stop it halfway through and mess with a bunch of wires and buttons before you can
    run the rest of the tests.
   
And then you asked yourself, 'How do I write my tests so that the device doesn't need to be connected?' You may have gone down the rabbit hole that is mocking, and then replaced large parts of pyserial with mock interfaces, and ultimately ended up with a test suite that was significantly more complex than the program it was meant to test.

With pytest-reserial, you don't have to worry about any of that. Just write your tests as if the device is always connected. Then, simply use the `reserial` fixture to record the serial traffic from passing tests, and replay it when the device isn't connected.

## Requirements

pytest-reserial depends on pytest and pyserial.

## Copyright

MIT License, (C) 2022 Alexander Bessman
