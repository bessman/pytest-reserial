import json

from serial import Serial

TEST_RX = b"\x01"
TEST_TX = b"\x02"
TEST_FILE = f"""
            import serial
            def test_reserial(reserial):
                s = serial.Serial(port="/dev/ttyUSB0")
                s.write({TEST_TX})
                assert s.read() == {TEST_RX}
            def test_reserial2(reserial):
                s = serial.Serial(port="/dev/ttyUSB0")
                s.write({TEST_TX})
                assert s.read() == {TEST_RX}
            """
TEST_FILE_BAD_TX = f"""
            import serial
            def test_reserial(reserial):
                s = serial.Serial(port="/dev/ttyUSB0")
                s.write({TEST_RX})
                assert s.read() == {TEST_RX}
            """
TEST_JSON = f"""
            {{
                "test_reserial": {{
                    "rx": {list(TEST_RX)},
                    "tx": {list(TEST_TX)}
                }},
                "test_reserial2": {{
                    "rx": {list(TEST_RX)},
                    "tx": {list(TEST_TX)}
                }}
            }}
            """


def test_record(monkeypatch, pytester):
    pytester.makepyfile(TEST_FILE)

    def patch_write(self: Serial, data: bytes) -> int:
        return len(data)

    def patch_read(self: Serial, size: int = 1) -> bytes:
        return TEST_RX

    def patch_open(self: Serial) -> None:
        self.is_open = True

    def patch_close(self: Serial) -> None:
        self.is_open = False

    monkeypatch.setattr(Serial, "write", patch_write)
    monkeypatch.setattr(Serial, "read", patch_read)
    monkeypatch.setattr(Serial, "open", patch_open)
    monkeypatch.setattr(Serial, "close", patch_close)
    result = pytester.runpytest("--record")

    with open("test_record.json", "r") as f:
        recording = json.load(f)

    assert recording == json.loads(TEST_JSON)
    assert result.ret == 0


def test_replay(pytester):
    pytester.makefile(".json", test_replay=TEST_JSON)
    pytester.makepyfile(TEST_FILE)
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
    pytester.makefile(".json", test_bad_tx=TEST_JSON)
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
        ".json",
        test_change_settings='{"test_reserial": {"tx": [], "rx": []}}',
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
