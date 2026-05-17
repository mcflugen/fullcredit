# Release Notes

## 0.1.0

### Feature

* Initial release
* Added `collect_git_contributors` API for extracting author name/email pairs
  from Git repositories
* Added `fullcredit contributors` CLI command
* Added nox sessions for linting, testing, coverage, and builds
* Added pre-commit configuration with formatting, linting, and type-checking hooks
* Added GitHub Actions CI workflow for building distributions, running tests/coverage,
  and publishing to PyPI/TestPyPI.
* Added a `fullcredit init` command to generate an initial author database from
  git contributor history.
* Added a `fullcredit mailmap` command to generate a *git* mailmap file from a
  `fullcredit` authors file.
* Added a `fullcredit authors` command to generate an author database from a list
  of contributors.
* Added a `fullcredit merge` command to combine multiple author databases into a
  single merged author list.
