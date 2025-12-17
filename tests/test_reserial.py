import json

import pytest
from serial import Serial
from serial.rfc2217 import Serial as RFC2217Serial

TEST_RX = b"\xfe"
TEST_RX_ENC = "/g=="
TEST_TX = b"\xff"
TEST_TX_ENC = "/w=="
TEST_RX_UTF8 = b"Hello World!\n"
TEST_RX_UTF8_ENC = "Hello World!\\n"
TEST_TX_UTF8 = b"Welcome!\r"
TEST_TX_UTF8_ENC = "Welcome!\\r"
STANDARD_SERIAL_CONNECTION_INIT = 'serial.Serial(port="/dev/ttyUSB0")'
SERIAL_FOR_URL_INIT = 'serial_for_url("rfc2217://127.0.0.1:8080")'


def make_test_file(
    serial_init: str,
    *,
    test_tx: bytes = TEST_TX,
    test_rx: bytes = TEST_RX,
    test2_tx: bytes = TEST_TX,
    test2_rx: bytes = TEST_RX,
) -> str:
    return f"""
            import serial
            from serial import serial_for_url
            def test_reserial(reserial):
                s = {serial_init}
                s.write({test_tx!r})
                assert s.in_waiting == {len(test_rx)}
                assert s.read() == {test_rx!r}
            def test_reserial2(reserial):
                s = {serial_init}
                s.write({test2_tx!r})
                assert s.read() == {test2_rx!r}
            """


def make_file_replay(
    serial_init: str, *, test_tx: bytes = TEST_TX, test_rx: bytes = TEST_RX
) -> str:
    return f"""
            import pytest
            import serial
            from serial import serial_for_url
            def test_reserial(reserial):
                s = {serial_init}
                s.write({test_tx!r})
                assert s.in_waiting == {len(test_rx)}
                assert s.read() == {test_rx!r}
                assert s.in_waiting == 0
                s.close()
                with pytest.raises(serial.PortNotOpenError):
                    s.read()
            def test_reserial2(reserial):
                s = {serial_init}
                s.write({test_tx!r})
                assert s.read() == {test_rx!r}
                s.close()
                with pytest.raises(serial.PortNotOpenError):
                    s.write({test_tx!r})
            """


def make_file_bad(serial_init: str) -> str:
    return f"""
            import serial
            from serial import serial_for_url
            def test_reserial(reserial):
                s = {serial_init}
                s.write({TEST_RX!r})
                assert s.read() == {TEST_RX!r}
            """


def make_file_update_existing(
    serial_init: str, *, test_tx: bytes = TEST_TX, test_rx: bytes = TEST_RX
) -> str:
    return f"""
            import serial
            from serial import serial_for_url
            def test_reserial(reserial):
                s = {serial_init}
                s.write({2 * test_tx})
                assert s.read() == {2 * test_rx}
                """


def make_change_settings_file(serial_init: str) -> str:
    return f"""
            import serial
            from serial import serial_for_url
            def test_reserial(reserial):
                s = {serial_init}
                s.timeout = 1
        """


TEST_JSONL = (
    f'{{"test_reserial": {{"rx": "{TEST_RX_ENC}", "tx": "{TEST_TX_ENC}"}}}}\n'
    f'{{"test_reserial2": {{"rx": "{TEST_RX_ENC}", "tx": "{TEST_TX_ENC}"}}}}\n'
)

TEST_JSONL_UTF8 = (
    f'{{"test_reserial": {{"rx": "{TEST_RX_UTF8_ENC}", "tx": "{TEST_TX_UTF8_ENC}", "rx_encoding": "utf-8", "tx_encoding": "utf-8"}}}}\n'
    f'{{"test_reserial2": {{"rx": "{TEST_RX_UTF8_ENC}", "tx": "{TEST_TX_UTF8_ENC}", "rx_encoding": "utf-8", "tx_encoding": "utf-8"}}}}\n'
)

TEST_JSONL_MIXED_UTF8_B64 = (
    f'{{"test_reserial": {{"rx": "{TEST_RX_ENC}", "tx": "{TEST_TX_UTF8_ENC}", "tx_encoding": "utf-8"}}}}\n'
    f'{{"test_reserial2": {{"rx": "{TEST_RX_UTF8_ENC}", "tx": "{TEST_TX_ENC}", "rx_encoding": "utf-8"}}}}\n'
)


@pytest.mark.parametrize(
    ("serial_init", "SerialClass"),
    [
        pytest.param(
            STANDARD_SERIAL_CONNECTION_INIT,
            Serial,
            id="standard serial connection",
        ),
        pytest.param(
            SERIAL_FOR_URL_INIT,
            RFC2217Serial,
            id="serial_for_url connection to RFC2217 server",
        ),
    ],
)
@pytest.mark.parametrize(
    ("test_tx", "test_rx", "test2_tx", "test2_rx", "expected_jsonl"),
    [
        pytest.param(
            TEST_TX,
            TEST_RX,
            TEST_TX,
            TEST_RX,
            TEST_JSONL,
            id="bytes that cannot decode to UTF-8 text",
        ),
        pytest.param(
            TEST_TX_UTF8,
            TEST_RX_UTF8,
            TEST_TX_UTF8,
            TEST_RX_UTF8,
            TEST_JSONL_UTF8,
            id="bytes that can decode to UTF-8 text",
        ),
        pytest.param(
            TEST_TX_UTF8,
            TEST_RX,
            TEST_TX,
            TEST_RX_UTF8,
            TEST_JSONL_MIXED_UTF8_B64,
            id="mixed UTF-8 and non-UTF-8 bytes",
        ),
    ],
)
def test_record(
    serial_init: str,
    SerialClass,
    test_tx: bytes,
    test_rx: bytes,
    test2_tx: bytes,
    test2_rx: bytes,
    expected_jsonl: str,
    monkeypatch,
    pytester,
):
    pytester.makepyfile(
        make_test_file(
            serial_init,
            test_tx=test_tx,
            test_rx=test_rx,
            test2_tx=test2_tx,
            test2_rx=test2_rx,
        )
    )

    def patch_write(self: SerialClass, data: bytes) -> int:
        return len(data)

    patched_read_call_count = 0

    def patch_read(self: SerialClass, size: int = 1) -> bytes:
        nonlocal patched_read_call_count
        patched_read_call_count += 1
        if patched_read_call_count <= 1:
            return test_rx
        else:
            return test2_rx

    @property
    def patch_in_waiting(self: SerialClass) -> int:
        return len(test_rx)

    def patch_open(self: SerialClass) -> None:
        self.is_open = True

    def patch_close(self: SerialClass) -> None:
        self.is_open = False

    monkeypatch.setattr(SerialClass, "write", patch_write)
    monkeypatch.setattr(SerialClass, "read", patch_read)
    monkeypatch.setattr(SerialClass, "open", patch_open)
    monkeypatch.setattr(SerialClass, "close", patch_close)
    monkeypatch.setattr(SerialClass, "in_waiting", patch_in_waiting)
    result = pytester.runpytest("--record")

    with open("test_record.jsonl") as f:
        recording = [json.loads(line) for line in f]

    expected = [json.loads(line) for line in expected_jsonl.splitlines()]

    assert recording == expected
    assert result.ret == 0


@pytest.mark.parametrize(
    ("serial_init", "SerialClass"),
    [
        pytest.param(
            STANDARD_SERIAL_CONNECTION_INIT,
            Serial,
            id="standard serial connection",
        ),
        pytest.param(
            SERIAL_FOR_URL_INIT,
            RFC2217Serial,
            id="standard serial connection",
        ),
    ],
)
@pytest.mark.parametrize(
    (
        "starting_jsonl",
        "expected_jsonl",
        "starting_test_rx",
        "starting_test_tx",
    ),
    [
        pytest.param(
            TEST_JSONL,
            (
                f'{{"test_reserial": {{"rx": "/v4=", "tx": "//8="}}}}\n'
                f'{{"test_reserial2": {{"rx": "{TEST_RX_ENC}", "tx": "{TEST_TX_ENC}"}}}}\n'
            ),
            TEST_RX,
            TEST_TX,
            id="bytes that cannot decode to UTF-8 text",
        ),
        pytest.param(
            TEST_JSONL_UTF8,
            (
                f'{{"test_reserial": {{"rx": "Hello World!\\nHello World!\\n", "tx": "Welcome!\\rWelcome!\\r", "rx_encoding": "utf-8", "tx_encoding": "utf-8"}}}}\n'
                f'{{"test_reserial2": {{"rx": "{TEST_RX_UTF8_ENC}", "tx": "{TEST_TX_UTF8_ENC}", "rx_encoding": "utf-8", "tx_encoding": "utf-8"}}}}\n'
            ),
            TEST_RX_UTF8,
            TEST_TX_UTF8,
            id="bytes that can decode to UTF-8 text",
        ),
    ],
)
def test_update_existing(
    serial_init: str,
    SerialClass,
    starting_jsonl: str,
    expected_jsonl: str,
    starting_test_rx: bytes,
    starting_test_tx: bytes,
    monkeypatch,
    pytester,
):
    pytester.makefile(".jsonl", test_update_existing=starting_jsonl)
    pytester.makepyfile(
        make_file_update_existing(
            serial_init, test_tx=starting_test_tx, test_rx=starting_test_rx
        )
    )

    def patch_write(self: SerialClass, data: bytes) -> int:
        return len(data)

    def patch_read(self: SerialClass, size: int = 1) -> bytes:
        return 2 * starting_test_rx

    def patch_open(self: SerialClass) -> None:
        self.is_open = True

    def patch_close(self: SerialClass) -> None:
        self.is_open = False

    monkeypatch.setattr(SerialClass, "write", patch_write)
    monkeypatch.setattr(SerialClass, "read", patch_read)
    monkeypatch.setattr(SerialClass, "open", patch_open)
    monkeypatch.setattr(SerialClass, "close", patch_close)
    result = pytester.runpytest("--record")

    with open("test_update_existing.jsonl") as f:
        recording = [json.loads(line) for line in f]

    expected = [json.loads(line) for line in expected_jsonl.splitlines()]

    assert recording == expected
    assert result.ret == 0


@pytest.mark.parametrize(
    "serial_init",
    [
        pytest.param(STANDARD_SERIAL_CONNECTION_INIT, id="standard serial connection"),
        pytest.param(
            SERIAL_FOR_URL_INIT, id="serial_for_url connection to RFC2217 server"
        ),
    ],
)
class TestSerialInit:
    """Tests parametrized by serial_init only."""

    def test_replay(self, serial_init: str, pytester):
        pytester.makefile(".jsonl", test_replay=TEST_JSONL)
        pytester.makepyfile(make_file_replay(serial_init))
        result = pytester.runpytest()
        assert result.ret == 0

    def test_invalid_option(self, serial_init: str, pytester):
        pytester.makepyfile(make_test_file(serial_init))
        result = pytester.runpytest("--disable-reserial", "--record")
        result.assert_outcomes(errors=2)

    def test_bad_tx(self, serial_init: str, pytester):
        pytester.makefile(".jsonl", test_bad_tx=TEST_JSONL)
        pytester.makepyfile(make_file_bad(serial_init))
        result = pytester.runpytest()
        result.assert_outcomes(errors=1, failed=1)

    def test_change_settings(self, serial_init: str, pytester):
        pytester.makefile(
            ".jsonl",
            test_change_settings='{"test_reserial": {"tx": "", "rx": ""}}',
        )
        pytester.makepyfile(make_change_settings_file(serial_init))
        result = pytester.runpytest()
        assert result.ret == 0


@pytest.mark.parametrize(
    "serial_module",
    [
        pytest.param("serial", id="main library"),
        pytest.param("serial.rfc2217", id="RFC2217 connection"),
    ],
)
def test_dont_patch(serial_module: str, pytester):
    pytester.makepyfile(
        f"""
        from {serial_module} import Serial
        real_read = Serial.read
        def test_something(reserial):
            assert Serial.read == real_read
        """
    )
    result = pytester.runpytest("--disable-reserial")
    assert result.ret == 0


def test_help_message(pytester):
    result = pytester.runpytest("--help")
    result.stdout.fnmatch_lines(
        [
            "reserial:",
            "*--record * Record serial traffic.",
            # the rest of the help text is wrapped into the next line in CI sometimes, so cannot do a strict match
            "*--disable-reserial * Disable reserial to allow standard*",
        ]
    )
    assert result.ret == 0


def test_no_traffic_for_test(pytester):
    pytester.makefile(".jsonl", test_no_traffic_for_test=TEST_JSONL)
    pytester.makepyfile(
        """
            import serial
            def test_reserial3(reserial):
                pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(errors=1)
