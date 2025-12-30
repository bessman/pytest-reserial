# Changelog

## [0.6.2] - Development

## [0.6.1] - 2025-12-30

### Fixed

- Fix FileExistsError on Windows ([`b9438c6`](https://github.com/bessman/pytest-reserial/commit/b9438c67b780293328cd9afe2f410f76de50bb60))

## [0.6.0] - 2025-12-18

### Changed

- __Breaking__: Encode traffic as UTF-8 if possible ([`5166bd5`](https://github.com/bessman/pytest-reserial/commit/5166bd51f753c90d7804a8b1a547d8ac20a77a98)) (Eli Fine)

## [0.5.1] - 2025-11-23

### Added

- Add support RFC2217 serial connections created via `serial.serial_for_url` ([`1e2e211`](https://github.com/bessman/pytest-reserial/commit/1e2e211eeec9a90466dc476a0daff132e58dd9b5)) (Eli Fine)

## [0.5.0] - 2025-11-17

### Added

- Add support for Python 3.14 ([`f46ea47`](https://github.com/bessman/pytest-reserial/commit/f46ea47a3eb8169306df7772906535a4f3aaff0f)) (Eli Fine)

### Changed

- __Breaking__: Default behavior with no command line arguments is to replay recorded communication ([`f46ea47`](https://github.com/bessman/pytest-reserial/commit/f46ea47a3eb8169306df7772906535a4f3aaff0f)) (Eli Fine)

## [0.4.3] - 2024-12-22

### Added

- Add support for Python 3.13 ([`c28f520`](https://github.com/bessman/pytest-reserial/commit/c28f5201222528867eea0d9e7daae8abbbb06cc6))

### Removed

- Remove support for EOL Python 3.8 ([`c28f520`](https://github.com/bessman/pytest-reserial/commit/c28f5201222528867eea0d9e7daae8abbbb06cc6))

### Fixed

- Patch `Serial.reset_input_buffer` during replay ([`2115eff`](https://github.com/bessman/pytest-reserial/commit/2115eff037b5003174b1705123b89c1594176713))

## [0.4.2] - 2024-07-23

### Fixed

- Raise `PortNotOpenError` on read/write from closed serial port ([`94c43b5`](https://github.com/bessman/pytest-reserial/commit/94c43b58c04adf1fd5f29d446acd976776874de1)) (Denis Patrikeev)
- Patch `Serial.in_waiting` during replay ([`358e778`](https://github.com/bessman/pytest-reserial/commit/358e778c85c3ae3190c05710a2321faf4e20a603)) (Denis Patrikeev)

## [0.4.1] - 2024-05-23

### Fixed

- Only patch `_reconfigure_port` during replay ([`4907c09`](https://github.com/bessman/pytest-reserial/commit/4907c09a40883b8324213a1d70377a580d478952))

## [0.4.0] - 2024-05-22

_This release changes the format for traffic log files. Use the provided `update_log.py`-script to update old logs to the new format._

### Changed

- __Breaking__: Store test recordings as JSON Lines instead of JSON ([`2b047d7`](https://github.com/bessman/pytest-reserial/commit/2b047d7cc96a06b201e7d25d316492e079835a61))
- __Breaking__: Store RX and TX bytes as base64 strings instead of lists ([`2b047d7`](https://github.com/bessman/pytest-reserial/commit/2b047d7cc96a06b201e7d25d316492e079835a61))

### Added

- Add script (`update_log.py`) to convert old log files to new format ([`ca14b9b`](https://github.com/bessman/pytest-reserial/commit/ca14b9be86ced3a58b417dc0d8b14afde97df86d))

### Removed

- Remove optional dependency on jsbeautifier ([`0ba5414`](https://github.com/bessman/pytest-reserial/commit/0ba54145e8362e187a479f8a61ac553263f7d8fa))

## [0.3.0] - 2024-02-07

### Changed

- __Breaking__: Raise `_pytest.outcomes.Failed` instead of `ValueError` on mismatch ([`b72d304`](https://github.com/bessman/pytest-reserial/commit/b72d304c1b21db524fd1eaf79c9aab91d9542b79))
- Split log files over multiple lines with `indent` ([`cd5aa41`](https://github.com/bessman/pytest-reserial/commit/cd5aa41d9be1877f68a45a4e069e1845dbb7f3c4))

### Added

- Add optional dependency on jsbeautifier to write prettier log files ([`cd5aa41`](https://github.com/bessman/pytest-reserial/commit/cd5aa41d9be1877f68a45a4e069e1845dbb7f3c4))
- Add Common Changelog ([`4f3168f`](https://github.com/bessman/pytest-reserial/commit/4f3168f989327a853e94cf5ffb7467c4826ba759))

### Fixed

- Fix malformed error message ([`45fd0ba`](https://github.com/bessman/pytest-reserial/commit/45fd0ba9e75f73ca320203216eda58433a0f6fbd))
- Fix `PytestUnraisableExceptionWarning` in `close` ([`4d711ac`](https://github.com/bessman/pytest-reserial/commit/4d711ac275af35f18f86a071e812952d92a053c9))

## [0.2.4] - 2023-08-31

### Fixed

- Fix log file truncated when running multiple tests ([`558ef1b`](https://github.com/bessman/pytest-reserial/commit/558ef1b31006aab7af7f3b14d582e8cdaf4bca3f))

## [0.2.3] - 2023-04-26

### Fixed

- Fix `AttributeError` when changing `timeout` ([`afa0c31`](https://github.com/bessman/pytest-reserial/commit/afa0c314f075d18794b1444ebd75ee4e36aff053))
- Fix type of logpath ([`f815f68`](https://github.com/bessman/pytest-reserial/commit/f815f6856f663be264604fd3ade484665fd914ec))

## [0.2.2] - 2022-11-29

### Fixed

- Fix relative path to log file ([`e87ad89`](https://github.com/bessman/pytest-reserial/commit/e87ad896f3ee727122f98f08f47634644de8ca1d))

## [0.2.1] - 2022-11-25

_Maintenance release._

## [0.2.0] - 2022-11-24

_Initial release._

[0.6.1]: https://github.com/bessman/pytest-reserial/releases/tag/0.6.1
[0.6.0]: https://github.com/bessman/pytest-reserial/releases/tag/0.6.0
[0.5.1]: https://github.com/bessman/pytest-reserial/releases/tag/0.5.1
[0.5.0]: https://github.com/bessman/pytest-reserial/releases/tag/0.5.0
[0.4.3]: https://github.com/bessman/pytest-reserial/releases/tag/0.4.3
[0.4.2]: https://github.com/bessman/pytest-reserial/releases/tag/0.4.2
[0.4.1]: https://github.com/bessman/pytest-reserial/releases/tag/0.4.1
[0.4.0]: https://github.com/bessman/pytest-reserial/releases/tag/0.4.0
[0.3.0]: https://github.com/bessman/pytest-reserial/releases/tag/0.3.0
[0.2.4]: https://github.com/bessman/pytest-reserial/releases/tag/v0.2.4
[0.2.3]: https://github.com/bessman/pytest-reserial/releases/tag/v0.2.3
[0.2.2]: https://github.com/bessman/pytest-reserial/releases/tag/v0.2.2
[0.2.1]: https://github.com/bessman/pytest-reserial/releases/tag/v0.2.1
[0.2.0]: https://github.com/bessman/pytest-reserial/releases/tag/v0.2.0
