import json

from serial import Serial

TEST_RX = b"\x01"
TEST_RX_ENC = "AQ=="
TEST_TX = b"\x02"
TEST_TX_ENC = "Ag=="
TEST_FILE = f"""
            import serial
            def test_reserial(reserial):
                s = serial.Serial(port="/dev/ttyUSB0")
                s.write({TEST_TX!r})
                assert s.in_waiting == {len(TEST_RX)}
                assert s.read() == {TEST_RX!r}
            def test_reserial2(reserial):
                s = serial.Serial(port="/dev/ttyUSB0")
                s.write({TEST_TX!r})
                assert s.read() == {TEST_RX!r}
            """
TEST_FILE_REPLAY = f"""
            import pytest
            import serial
            def test_reserial(reserial):
                s = serial.Serial(port="/dev/ttyUSB0")
                s.write({TEST_TX!r})
                assert s.in_waiting == {len(TEST_RX)}
                assert s.read() == {TEST_RX!r}
                assert s.in_waiting == 0
                s.close()
                with pytest.raises(serial.PortNotOpenError):
                    s.read()
            def test_reserial2(reserial):
                s = serial.Serial(port="/dev/ttyUSB0")
                s.write({TEST_TX!r})
                assert s.read() == {TEST_RX!r}
                s.close()
                with pytest.raises(serial.PortNotOpenError):
                    s.write({TEST_TX!r})
            """
TEST_FILE_BAD_TX = f"""
                    import serial
                    def test_reserial(reserial):
                        s = serial.Serial(port="/dev/ttyUSB0")
                        s.write({TEST_RX!r})
                        assert s.read() == {TEST_RX!r}
                    """
TEST_JSONL = (
    f'{{"test_reserial": {{"rx": "{TEST_RX_ENC}", "tx": "{TEST_TX_ENC}"}}}}\n'
    f'{{"test_reserial2": {{"rx": "{TEST_RX_ENC}", "tx": "{TEST_TX_ENC}"}}}}\n'
)


def test_record(monkeypatch, pytester):
    pytester.makepyfile(TEST_FILE)

    def patch_write(self: Serial, data: bytes) -> int:
        return len(data)

    def patch_read(self: Serial, size: int = 1) -> bytes:
        return TEST_RX

    @property
    def patch_in_waiting(self: Serial) -> int:
        return len(TEST_RX)

    def patch_open(self: Serial) -> None:
        self.is_open = True

    def patch_close(self: Serial) -> None:
        self.is_open = False

    monkeypatch.setattr(Serial, "write", patch_write)
    monkeypatch.setattr(Serial, "read", patch_read)
    monkeypatch.setattr(Serial, "open", patch_open)
    monkeypatch.setattr(Serial, "close", patch_close)
    monkeypatch.setattr(Serial, "in_waiting", patch_in_waiting)
    result = pytester.runpytest("--record")

    with open("test_record.jsonl", "r") as f:
        recording = [json.loads(line) for line in f.readlines()]

    expected = [json.loads(line) for line in TEST_JSONL.splitlines()]

    assert recording == expected
    assert result.ret == 0


def test_update_existing(monkeypatch, pytester):
    pytester.makefile(".jsonl", test_update_existing=TEST_JSONL)
    pytester.makepyfile(
        f"""
        import serial
        def test_reserial(reserial):
            s = serial.Serial(port="/dev/ttyUSB0")
            s.write({2 * TEST_TX})
            assert s.read() == {2 * TEST_RX}
        """
    )

    def patch_write(self: Serial, data: bytes) -> int:
        return len(data)

    def patch_read(self: Serial, size: int = 1) -> bytes:
        return 2 * TEST_RX

    def patch_open(self: Serial) -> None:
        self.is_open = True

    def patch_close(self: Serial) -> None:
        self.is_open = False

    monkeypatch.setattr(Serial, "write", patch_write)
    monkeypatch.setattr(Serial, "read", patch_read)
    monkeypatch.setattr(Serial, "open", patch_open)
    monkeypatch.setattr(Serial, "close", patch_close)
    result = pytester.runpytest("--record")

    with open("test_update_existing.jsonl", "r") as f:
        recording = [json.loads(line) for line in f.readlines()]

    expected_rx_enc = "AQE="
    expected_tx_enc = "AgI="
    expected_jsonl = (
        f'{{"test_reserial": {{"rx": "{expected_rx_enc}", "tx": "{expected_tx_enc}"}}}}\n'
        f'{{"test_reserial2": {{"rx": "{TEST_RX_ENC}", "tx": "{TEST_TX_ENC}"}}}}\n'
    )

    expected = [json.loads(line) for line in expected_jsonl.splitlines()]

    assert recording == expected
    assert result.ret == 0


def test_replay(pytester):
    pytester.makefile(".jsonl", test_replay=TEST_JSONL)
    pytester.makepyfile(TEST_FILE_REPLAY)
    result = pytester.runpytest("--replay")
    assert result.ret == 0


def test_dont_patch(pytester):
    pytester.makepyfile(
        """
        from serial import Serial
        real_read = Serial.read
        def test_something(reserial):
            assert Serial.read == real_read
        """
    )
    result = pytester.runpytest()
    assert result.ret == 0


def test_invalid_option(pytester):
    pytester.makepyfile(TEST_FILE)
    result = pytester.runpytest("--replay", "--record")
    result.assert_outcomes(errors=2)


def test_bad_tx(pytester):
    pytester.makefile(".jsonl", test_bad_tx=TEST_JSONL)
    pytester.makepyfile(TEST_FILE_BAD_TX)
    result = pytester.runpytest("--replay")
    result.assert_outcomes(errors=1, failed=1)


def test_help_message(pytester):
    result = pytester.runpytest("--help")
    result.stdout.fnmatch_lines(
        [
            "reserial:",
            "*--record * Record serial traffic.",
            "*--replay * Replay serial traffic.",
        ]
    )
    assert result.ret == 0


def test_change_settings(pytester):
    pytester.makefile(
        ".jsonl",
        test_change_settings='{"test_reserial": {"tx": "", "rx": ""}}',
    )
    pytester.makepyfile(
        """
            import serial
            def test_reserial(reserial):
                s = serial.Serial(port="/dev/ttyUSB0")
                s.timeout = 1
        """
    )
    result = pytester.runpytest("--replay")
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
    result = pytester.runpytest("--replay")
    result.assert_outcomes(errors=1)
