# Changelog

## [0.3.1] - Development

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

[0.3.0]: https://github.com/bessman/pytest-reserial/releases/tag/0.3.0
[0.2.4]: https://github.com/bessman/pytest-reserial/releases/tag/v0.2.4
[0.2.3]: https://github.com/bessman/pytest-reserial/releases/tag/v0.2.3
[0.2.2]: https://github.com/bessman/pytest-reserial/releases/tag/v0.2.2
[0.2.1]: https://github.com/bessman/pytest-reserial/releases/tag/v0.2.1
[0.2.0]: https://github.com/bessman/pytest-reserial/releases/tag/v0.2.0
