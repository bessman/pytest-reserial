"""Record or replay serial traffic when running tests."""

import json
from enum import IntEnum
from pathlib import Path
from typing import Callable, Dict, Generator, List, Tuple

import pytest
from serial import Serial  # type: ignore[import]


def pytest_addoption(parser: pytest.Parser) -> None:  # noqa: D103
    group = parser.getgroup("reserial")
    group.addoption(
        "--record", action="store_true", default=False, help="Record serial traffic."
    )
    group.addoption(
        "--replay", action="store_true", default=False, help="Replay serial traffic."
    )


class Mode(IntEnum):
    """Mode of operation, selected by the 'replay' and 'record' flags to pytest."""

    DONT_PATCH = 0
    REPLAY = 1
    RECORD = 2
    INVALID = 3


def reconfigure_port_patch(
    self: Serial, force_update: bool = False  # pylint: disable=unused-argument
) -> None:
    """Don't try to set parameters on the mocked port.

    When changing settings such as timeout, parity, stop bits, etc. the
    _reconfigure_port method is called. It operates directly on the underlying operating
    system resource, which doesn't exist in reserial. Therefore, this patch is required.
    """


@pytest.fixture
def reserial(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> Generator[None, None, None]:
    """Record or replay serial traffic.

    Raises
    ------
    ValueError
        If less data than expected was read or written during replay.
    """
    record = request.config.getoption("--record")
    replay = request.config.getoption("--replay")
    mode = Mode(replay | record << 1)

    logpath = Path(request.path).parent / (Path(request.path).stem + ".json")
    testname = request.node.name
    log = get_traffic_log(mode, logpath, testname)

    read_patch, write_patch, open_patch, close_patch = get_patched_methods(mode, log)
    monkeypatch.setattr(Serial, "read", read_patch)
    monkeypatch.setattr(Serial, "write", write_patch)
    monkeypatch.setattr(Serial, "open", open_patch)
    monkeypatch.setattr(Serial, "close", close_patch)
    monkeypatch.setattr(Serial, "_reconfigure_port", reconfigure_port_patch)

    yield

    if mode == Mode.RECORD:
        write_log(log, logpath, testname)
        return

    if log["rx"] or log["tx"]:
        raise ValueError("Not empty")


def get_traffic_log(mode: Mode, logpath: Path, testname: str) -> Dict[str, List[int]]:
    """Load recorded traffic (replay) or create an empty log (record).

    Parameters
    ----------
    mode : Mode
        The requested mode of operation, i.e. `REPLAY`, `RECORD`, or `DONT_PATCH`.
    logpath: str
        The name of the file where recorded traffic is logged.
    testname: str
        The name of the currently running test, which is used as a key in the log file.

    Returns
    -------
    log : dict[str, list[int]]
        Dictionary with keys "rx" and "tx", with corresponding lists of received and
        transmitted data. If `mode` is `RECORD` or `DONT_PATCH`, the lists are empty.

    Raises
    ------
    ValueError
        If both '--replay' and '--record' were specified.
    """
    if mode == Mode.INVALID:
        raise ValueError("Choose one of 'replay' or 'record', not both.")

    log: Dict[str, List[int]] = {"rx": [], "tx": []}

    if mode == Mode.REPLAY:
        with open(logpath, "r", encoding="utf-8") as logfile:
            logs = json.load(logfile)
        log = logs[testname]

    return log


def get_patched_methods(
    mode: Mode, log: Dict[str, List[int]]
) -> Tuple[
    Callable[[Serial, int], bytes],
    Callable[[Serial, bytes], int],
    Callable[[Serial], None],
    Callable[[Serial], None],
]:
    """Return patched read, write, open, and closed methods.

    The methods should be monkeypatched over the corresponding `Serial` methods.

    Parameters
    ----------
    mode: Mode
        The requested mode of operation, i.e. `REPLAY`, `RECORD`, or `DONT_PATCH`.
    log: dict[str, list[int]]
        Dictionary holding logged traffic (replay) / where traffic will be logged to
        (record). If mode is `DONT_PATCH`, this parameter is ignored.

    Returns
    -------
    read_patch: Callable[[Serial, int], bytes]
        Monkeypatch this over `Serial.read`.
    write_patch: Callable[[Serial, bytes], int]
        Monkeypatch this over `Serial.write`.
    open_patch: Callable[[Serial], None]
        Monkeypatch this over `Serial.open`.
    close_patch: Callable[[Serial], None]
        Monkeypatch this over `Serial.close`.
    """
    if mode == Mode.REPLAY:
        return get_replay_methods(log)
    if mode == Mode.RECORD:
        return get_record_methods(log)
    return Serial.read, Serial.write, Serial.open, Serial.close


def get_replay_methods(
    log: Dict[str, List[int]]
) -> Tuple[
    Callable[[Serial, int], bytes],
    Callable[[Serial, bytes], int],
    Callable[[Serial], None],
    Callable[[Serial], None],
]:
    """Return patched read, write, open, and close methods for replaying logged traffic.

    Parameters
    ----------
    log: dict[str, list[int]]
        Dictionary holding logged traffic.

    Returns
    -------
    replay_read: Callable[[Serial, int], bytes]
        Reads RX traffic from log file instead of from bus.
    replay_write: Callable[[Serial, bytes], int]
        Compares written data with logged TX traffic instead of writing to bus.
    replay_open: Callable[[Serial], None]
        Sets `Serial.is_open` to `True`.
    replay_close: Callable[[Serial], None]
        Sets `Serial.is_open` to `False`.
    """

    def replay_write(
        self: Serial,  # pylint: disable=unused-argument
        data: bytes,
    ) -> int:
        """Compare TX data to recording instead of writing to the bus.

        Monkeypatch this method over Serial.write to replay traffic. Parameters and
        return values are identical to Serial.write.

        Raises
        ------
        ValueError
            If written data does not match recorded data.
        """
        if list(data) == log["tx"][: len(data)]:
            log["tx"] = log["tx"][len(data) :]
        else:
            raise ValueError(
                "Written data does not match recorded data: "
                "f{data} != {traffic_log['tx'][: len(data)]}"
            )

        return len(data)

    def replay_read(
        self: Serial,  # pylint: disable=unused-argument
        size: int = 1,
    ) -> bytes:
        """Replay RX data from recording instead of reading from the bus.

        Monkeypatch this method over Serial.read to replay traffic. Parameters and
        return values are identical to Serial.read.
        """
        data = log["rx"][:size]
        log["rx"] = log["rx"][size:]
        return bytes(data)

    return replay_read, replay_write, replay_open, replay_close


# The open/close method patches don't need access to logs, so they can stay down here.
def replay_open(self: Serial) -> None:
    """Pretend that port was opened."""
    self.is_open = True


def replay_close(self: Serial) -> None:
    """Pretend that port was closed."""
    self.is_open = False


def get_record_methods(
    log: Dict[str, List[int]]
) -> Tuple[
    Callable[[Serial, int], bytes],
    Callable[[Serial, bytes], int],
    Callable[[Serial], None],
    Callable[[Serial], None],
]:
    """Return patched read, write, open, and close methods for recording traffic.

    Parameters
    ----------
    log: dict[str, list[int]]
        Dictionary where recorded traffic will be logged.

    Returns
    -------
    record_read: Callable[[Serial, int], bytes]
        Logs RX data read from the bus.
    record_write: Callable[[Serial, bytes], int]
        Logs TX data before writing it to the bus.
    record_open: Callable[[Serial], None]
        Does not need to be patched when recording, so this is `Serial.open`.
    record_close: Callable[[Serial], None]
        Does not need to be patched when recording, so this is `Serial.close`.
    """
    real_read = Serial.read
    real_write = Serial.write

    def record_write(self: Serial, data: bytes) -> int:
        """Record TX data before writing to the bus.

        Monkeypatch this method over Serial.write to record traffic. Parameters and
        return values are identical to Serial.write.
        """
        log["tx"] += list(data)
        written: int = real_write(self, data)
        return written

    def record_read(self: Serial, size: int = 1) -> bytes:
        """Record RX data after reading from the bus.

        Monkeypatch this method over Serial.read to record traffic. Parameters and
        return values are identical to Serial.read.
        """
        data: bytes = real_read(self, size)
        log["rx"] += list(data)
        return data

    return record_read, record_write, Serial.open, Serial.close


def write_log(
    log: Dict[str, List[int]],
    logpath: Path,
    testname: str,
) -> None:
    """Write recorded traffic to log file.

    Parameters
    ----------
    log: dict[str, list[int]]
        Dictionary holding recorded traffic.
    logpath: str
        The name of the file where recorded traffic is logged.
    testname: str
        The name of the currently running test, which is used as a key in the log file.
    """
    try:
        # If the file exists, read its contents.
        with open(logpath, mode="r", encoding="utf-8") as logfile:
            logs = json.load(logfile)
    except FileNotFoundError:
        logs = {}

    logs[testname] = log

    with open(logpath, mode="w", encoding="utf-8") as logfile:
        # Wipe the file if it exists, or create a new file if it doesn't.
        json.dump(logs, logfile)
