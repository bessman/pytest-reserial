import json
from pathlib import Path

import pytest
from serial import Serial


@pytest.fixture(scope="module")
def default_logdir(request):
    return Path(request.fspath).parent / "traffic_logs"


def pytest_addoption(parser):
    parser.addoption("--record", action="store_true", default=False)
    parser.addoption("--replay", action="store_true", default=False)
    parser.addoption("--logdir", action="store", default=None)


@pytest.fixture
def reserial(monkeypatch, request, default_logdir):
    record = request.config.getoption("--record")
    replay = request.config.getoption("--replay")
    logdir = request.config.getoption("--logdir")
    logdir = logdir if logdir else default_logdir
    logdir = Path(logdir) / Path(request.fspath).stem
    logname = request.node.name + ".json"
    logpath = logdir / logname

    if record:
        TRAFFIC_LOG = {"tx": [], "rx": []}
    elif replay:
        with open(logpath, "r") as log:
            TRAFFIC_LOG = json.load(log)

        def patch_open(self):
            self.is_open = True

        def patch_close(self):
            self.is_open = False

        monkeypatch.setattr(Serial, "open", patch_open)
        monkeypatch.setattr(Serial, "close", patch_close)
    else:
        # Neither 'record' or 'replay' was requested, so don't patch Serial.
        yield
        return

    real_write = Serial.write
    real_read = Serial.read

    # Store any outgoing data before writing it to the bus.
    def rec_write(self, data):
        nonlocal TRAFFIC_LOG
        TRAFFIC_LOG["tx"] += list(data)
        real_write(self, data)

    # Store any incoming data.
    def rec_read(self, size=1):
        data = real_read(self, size)
        nonlocal TRAFFIC_LOG
        TRAFFIC_LOG["rx"] += list(data)
        return data

    # Check that outgoing data matches recorded data.
    def replay_write(self, data):
        nonlocal TRAFFIC_LOG
        if list(data) == TRAFFIC_LOG["tx"][: len(data)]:
            TRAFFIC_LOG["tx"] = TRAFFIC_LOG["tx"][len(data) :]
        else:
            raise ValueError(
                "Written data does not match recorded data: "
                "f{data} != {TRAFFIC_LOG['tx'][: len(data)]}"
            )

    # Return recorded incoming data.
    def replay_read(self, size=1):
        nonlocal TRAFFIC_LOG
        data = TRAFFIC_LOG["rx"][:size]
        TRAFFIC_LOG["rx"] = TRAFFIC_LOG["rx"][size:]
        return bytes(data)

    monkeypatch.setattr(Serial, "write", rec_write if record else replay_write)
    monkeypatch.setattr(Serial, "read", rec_read if record else replay_read)

    yield

    if record:
        with open(logpath, "w") as log:
            json.dump(TRAFFIC_LOG, log)
        return

    if TRAFFIC_LOG["rx"] or TRAFFIC_LOG["tx"]:
        raise ValueError("Not empty")
