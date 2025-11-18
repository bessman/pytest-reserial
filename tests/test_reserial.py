import json

import pytest
from serial import Serial
from serial.rfc2217 import Serial as RFC2217Serial

TEST_RX = b"\x01"
TEST_RX_ENC = "AQ=="
TEST_TX = b"\x02"
TEST_TX_ENC = "Ag=="
STANDARD_SERIAL_CONNECTION_INIT = 'serial.Serial(port="/dev/ttyUSB0")'
SERIAL_FOR_URL_INIT = 'serial_for_url("rfc2217://127.0.0.1:8080")'


def make_test_file(serial_init: str) -> str:
    return f"""
            import serial
            from serial import serial_for_url
            def test_reserial(reserial):
                s = {serial_init}
                s.write({TEST_TX!r})
                assert s.in_waiting == {len(TEST_RX)}
                assert s.read() == {TEST_RX!r}
            def test_reserial2(reserial):
                s = {serial_init}
                s.write({TEST_TX!r})
                assert s.read() == {TEST_RX!r}
            """


def make_file_replay(serial_init: str) -> str:
    return f"""
            import pytest
            import serial
            from serial import serial_for_url
            def test_reserial(reserial):
                s = {serial_init}
                s.write({TEST_TX!r})
                assert s.in_waiting == {len(TEST_RX)}
                assert s.read() == {TEST_RX!r}
                assert s.in_waiting == 0
                s.close()
                with pytest.raises(serial.PortNotOpenError):
                    s.read()
            def test_reserial2(reserial):
                s = {serial_init}
                s.write({TEST_TX!r})
                assert s.read() == {TEST_RX!r}
                s.close()
                with pytest.raises(serial.PortNotOpenError):
                    s.write({TEST_TX!r})
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


TEST_JSONL = (
    f'{{"test_reserial": {{"rx": "{TEST_RX_ENC}", "tx": "{TEST_TX_ENC}"}}}}\n'
    f'{{"test_reserial2": {{"rx": "{TEST_RX_ENC}", "tx": "{TEST_TX_ENC}"}}}}\n'
)


@pytest.mark.parametrize(
    ("test_file", "SerialClass"),
    [
        pytest.param(
            make_test_file(STANDARD_SERIAL_CONNECTION_INIT),
            Serial,
            id="standard serial connection",
        ),
        pytest.param(
            make_test_file(SERIAL_FOR_URL_INIT),
            RFC2217Serial,
            id="serial_for_url connection to RFC2217 server",
        ),
    ],
)
def test_record(test_file: str, SerialClass, monkeypatch, pytester):
    pytester.makepyfile(test_file)

    def patch_write(self: SerialClass, data: bytes) -> int:
        return len(data)

    def patch_read(self: SerialClass, size: int = 1) -> bytes:
        return TEST_RX

    @property
    def patch_in_waiting(self: SerialClass) -> int:
        return len(TEST_RX)

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

    expected = [json.loads(line) for line in TEST_JSONL.splitlines()]

    assert recording == expected
    assert result.ret == 0


@pytest.mark.parametrize(
    ("test_file", "SerialClass"),
    [
        pytest.param(
            f"""
        import serial
        def test_reserial(reserial):
            s = serial.Serial(port="/dev/ttyUSB0")
            s.write({2 * TEST_TX})
            assert s.read() == {2 * TEST_RX}
        """,
            Serial,
            id="standard serial connection",
        ),
        pytest.param(
            f"""
        from serial import serial_for_url
        def test_reserial(reserial):
            s = serial_for_url("rfc2217://localhost:1234")
            s.write({2 * TEST_TX})
            assert s.read() == {2 * TEST_RX}
        """,
            RFC2217Serial,
            id="standard serial connection",
        ),
    ],
)
def test_update_existing(test_file: str, SerialClass, monkeypatch, pytester):
    pytester.makefile(".jsonl", test_update_existing=TEST_JSONL)
    pytester.makepyfile(test_file)

    def patch_write(self: SerialClass, data: bytes) -> int:
        return len(data)

    def patch_read(self: SerialClass, size: int = 1) -> bytes:
        return 2 * TEST_RX

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

    expected_rx_enc = "AQE="
    expected_tx_enc = "AgI="
    expected_jsonl = (
        f'{{"test_reserial": {{"rx": "{expected_rx_enc}", "tx": "{expected_tx_enc}"}}}}\n'
        f'{{"test_reserial2": {{"rx": "{TEST_RX_ENC}", "tx": "{TEST_TX_ENC}"}}}}\n'
    )

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
def test_replay(serial_init: str, pytester):
    pytester.makefile(".jsonl", test_replay=TEST_JSONL)
    pytester.makepyfile(make_file_replay(serial_init))
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


@pytest.mark.parametrize(
    "serial_init",
    [
        pytest.param(STANDARD_SERIAL_CONNECTION_INIT, id="standard serial connection"),
        pytest.param(
            SERIAL_FOR_URL_INIT, id="serial_for_url connection to RFC2217 server"
        ),
    ],
)
def test_invalid_option(serial_init: str, pytester):
    pytester.makepyfile(make_test_file(serial_init))
    result = pytester.runpytest("--disable-reserial", "--record")
    result.assert_outcomes(errors=2)


@pytest.mark.parametrize(
    "serial_init",
    [
        pytest.param(STANDARD_SERIAL_CONNECTION_INIT, id="standard serial connection"),
        pytest.param(
            SERIAL_FOR_URL_INIT, id="serial_for_url connection to RFC2217 server"
        ),
    ],
)
def test_bad_tx(serial_init: str, pytester):
    pytester.makefile(".jsonl", test_bad_tx=TEST_JSONL)
    pytester.makepyfile(make_file_bad(serial_init))
    result = pytester.runpytest()
    result.assert_outcomes(errors=1, failed=1)


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


@pytest.mark.parametrize(
    "test_file",
    [
        pytest.param(
            """
            import serial
            def test_reserial(reserial):
                s = serial.Serial(port="/dev/ttyUSB0")
                s.timeout = 1
        """,
            id="main library",
        ),
        pytest.param(
            """
            from serial import serial_for_url
            def test_reserial(reserial):
                s = serial_for_url("rfc2217://localhost:1234")
                s.timeout = 1
        """,
            id="RFC2217 connection",
        ),
    ],
)
def test_change_settings(test_file: str, pytester):
    pytester.makefile(
        ".jsonl",
        test_change_settings='{"test_reserial": {"tx": "", "rx": ""}}',
    )
    pytester.makepyfile(test_file)
    result = pytester.runpytest()
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
