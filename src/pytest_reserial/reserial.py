"""Record or replay serial traffic when running tests."""

from __future__ import annotations

import base64
import json
from enum import IntEnum
from pathlib import Path
from typing import Callable, Dict, Iterator, Literal, Tuple

import pytest
from serial import PortNotOpenError, Serial  # type: ignore[import-untyped]

TrafficLog = Dict[Literal["rx", "tx"], bytes]
PatchMethods = Tuple[
    Callable[[Serial, int], bytes],  # read
    Callable[[Serial, bytes], int],  # write
    Callable[[Serial], None],  # open
    Callable[[Serial], None],  # close
    Callable[[Serial, bool], None],  # _reconfigure_port
    Callable[[Serial], int],  # in_waiting
]


def pytest_addoption(parser: pytest.Parser) -> None:  # noqa: D103
    group = parser.getgroup("reserial")
    group.addoption(
        "--record",
        action="store_true",
        default=False,
        help="Record serial traffic.",
    )
    group.addoption(
        "--replay",
        action="store_true",
        default=False,
        help="Replay serial traffic.",
    )


class Mode(IntEnum):
    """Mode of operation, selected by the 'replay' and 'record' flags to pytest."""

    DONT_PATCH = 0
    REPLAY = 1
    RECORD = 2
    INVALID = 3


@pytest.fixture()
def reserial(
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> Iterator[None]:
    """Record or replay serial traffic.

    Raises
    ------
    _pytest.outcomes.Failed
        If less data than expected was read or written during replay.
    """
    record = request.config.getoption("--record")
    replay = request.config.getoption("--replay")
    mode = Mode(replay | record << 1)

    log_path = Path(request.path).parent / (Path(request.path).stem + ".jsonl")
    test_name = request.node.name
    log = get_traffic_log(mode, log_path, test_name)

    (
        read_patch,
        write_patch,
        open_patch,
        close_patch,
        reconfigure_port_patch,
        in_waiting_patch,
    ) = get_patched_methods(mode, log)
    monkeypatch.setattr(Serial, "read", read_patch)
    monkeypatch.setattr(Serial, "write", write_patch)
    monkeypatch.setattr(Serial, "open", open_patch)
    monkeypatch.setattr(Serial, "close", close_patch)
    monkeypatch.setattr(Serial, "_reconfigure_port", reconfigure_port_patch)
    monkeypatch.setattr(Serial, "in_waiting", in_waiting_patch)

    yield

    if mode == Mode.RECORD:
        write_log(log, log_path, test_name)
        return

    if log["rx"] or log["tx"]:
        msg = (
            "Some messages where not replayed:}\n"
            f"Remaining RX: {len(log['rx'])}\n"
            f"Remaining TX: {len(log['tx'])}"
        )
        pytest.fail(msg)


def get_traffic_log(mode: Mode, log_path: Path, test_name: str) -> TrafficLog:
    """Load recorded traffic (replay) or create an empty log (record).

    Parameters
    ----------
    mode : Mode
        The requested mode of operation, i.e. `REPLAY`, `RECORD`, or `DONT_PATCH`.
    log_path: str
        The name of the file where recorded traffic is logged.
    test_name: str
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
        If no the test has no recorded traffic .
    """
    if mode == Mode.INVALID:
        msg = "Choose one of 'replay' or 'record', not both"
        raise ValueError(msg)

    log: TrafficLog = {"rx": b"", "tx": b""}

    if mode == Mode.REPLAY:
        with Path.open(log_path) as fin:
            for line in fin:
                if log := json.loads(line).get(test_name):
                    break
            else:
                msg = f"No recorded traffic for test: {test_name}"
                raise ValueError(msg)

            log["rx"] = base64.b64decode(log["rx"])
            log["tx"] = base64.b64decode(log["tx"])

    return log


def get_patched_methods(mode: Mode, log: TrafficLog) -> PatchMethods:
    """Return patched read, write, open, etc methods.

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
    _reconfigure_port_patch: Callable[[Serial, bool], None]
        Monkeypatch this over `Serial._reconfigure_port`.
    in_waiting_patch: Callable[[Serial], int]
        Monkeypatch this over `Serial.in_waiting`.
    """
    if mode == Mode.REPLAY:
        return get_replay_methods(log)
    if mode == Mode.RECORD:
        return get_record_methods(log)
    return (
        Serial.read,
        Serial.write,
        Serial.open,
        Serial.close,
        Serial._reconfigure_port,  # noqa: SLF001
        Serial.in_waiting,
    )


def get_replay_methods(log: TrafficLog) -> PatchMethods:
    """Return patched read, write, open, etc methods for replaying logged traffic.

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
    replay_reconfigure_port: Callable[[Serial, bool], None]
        No-op
    record_in_waiting: Callable[[Serial], int]
        Return the number of bytes of RX traffic left to replay.

    """

    def replay_write(
        self: Serial,
        data: bytes,
    ) -> int:
        """Compare TX data to recording instead of writing to the bus.

        Monkeypatch this method over Serial.write to replay traffic. Parameters and
        return values are identical to Serial.write.

        Raises
        ------
        _pytest.outcomes.Failed
            If written data does not match recorded data.
        """
        if not self.is_open:
            raise PortNotOpenError

        if data == log["tx"][: len(data)]:
            log["tx"] = log["tx"][len(data) :]
        else:
            msg = (
                "Written data does not match recorded data: "
                f"{data!r} != {log['tx'][: len(data)]!r}"
            )
            pytest.fail(msg)

        return len(data)

    def replay_read(
        self: Serial,
        size: int = 1,
    ) -> bytes:
        """Replay RX data from recording instead of reading from the bus.

        Monkeypatch this method over Serial.read to replay traffic. Parameters and
        return values are identical to Serial.read.
        """
        if not self.is_open:
            raise PortNotOpenError

        data = log["rx"][:size]
        log["rx"] = log["rx"][size:]
        return bytes(data)

    @property  # type: ignore[misc]
    def replay_in_waiting(
        self: Serial,  # noqa:ARG001
    ) -> int:
        """Return the number of bytes in RX data left to replay."""
        return len(log["rx"])

    return (
        replay_read,
        replay_write,
        replay_open,
        replay_close,
        replay_reconfigure_port,
        replay_in_waiting,
    )


# The open/close method patches don't need access to logs, so they can stay down here.
def replay_open(self: Serial) -> None:
    """Pretend that port was opened."""
    self.is_open = True
    self.fd = None


def replay_close(self: Serial) -> None:
    """Pretend that port was closed."""
    self.is_open = False


def replay_reconfigure_port(
    self: Serial,  # noqa: ARG001
    force_update: bool = False,  # noqa: ARG001, FBT001, FBT002
) -> None:
    """Don't try to set parameters on the mocked port.

    When changing settings such as timeout, parity, stop bits, etc. the
    _reconfigure_port method is called. It operates directly on the underlying operating
    system resource, which doesn't exist in reserial. Therefore, this patch is required.
    """


def get_record_methods(log: TrafficLog) -> PatchMethods:
    """Return patched read, write, open, etc methods for recording traffic.

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
    record_reconfigure_port: Callable[[Serial, bool], None]
        Does not need to be patched when recording,
        so this is `Serial._reconfigure_port`.
    record_in_waiting: Callable[[Serial], int]
        Does not need to be patched when recording, so this is `Serial.in_waiting`.

    """
    real_read = Serial.read
    real_write = Serial.write

    def record_write(self: Serial, data: bytes) -> int:
        """Record TX data before writing to the bus.

        Monkeypatch this method over Serial.write to record traffic. Parameters and
        return values are identical to Serial.write.
        """
        log["tx"] += data
        written: int = real_write(self, data)
        return written

    def record_read(self: Serial, size: int = 1) -> bytes:
        """Record RX data after reading from the bus.

        Monkeypatch this method over Serial.read to record traffic. Parameters and
        return values are identical to Serial.read.
        """
        data: bytes = real_read(self, size)
        log["rx"] += data
        return data

    return (
        record_read,
        record_write,
        Serial.open,
        Serial.close,
        Serial._reconfigure_port,  # noqa: SLF001
        Serial.in_waiting,
    )


def write_log(
    log: TrafficLog,
    log_path: Path,
    test_name: str,
) -> None:
    """Write recorded traffic to log file.

    Parameters
    ----------
    log: dict[str, list[int]]
        Dictionary holding recorded traffic.
    log_path: str
        The name of the file where recorded traffic is logged.
    test_name: str
        The name of the currently running test, which is used as a key in the log file.
    """
    # Make sure log file exists.
    log_path.touch()
    # Write new data to temporary file.
    tmp_path = Path(test_name + "_" + hex(abs(hash(test_name))).lstrip("0x"))

    with log_path.open("r") as fin, tmp_path.open("w") as fout:
        seen = False
        rx = base64.b64encode(bytes(log["rx"])).decode("ascii")
        tx = base64.b64encode(bytes(log["tx"])).decode("ascii")
        new_line = json.dumps({test_name: {"rx": rx, "tx": tx}}) + "\n"

        # Recorded traffic is stored as JSON Lines. Parse one line at a time.
        for old_line in fin:
            test_data = json.loads(old_line)

            # Each record contains a single key.
            if test_name in test_data:
                fout.write(new_line)
                seen = True
                continue

            fout.write(old_line)

        if not seen:
            fout.write(new_line)

    # Overwrite old log file.
    Path(tmp_path).rename(log_path)
