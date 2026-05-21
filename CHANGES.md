# Release Notes

## 0.1.0

### Features

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
* Added a `fullcredit sort` command to sort an author database by name, last
  name, GitHub username, or number of commits in a repository.
* Renamed `AuthorList` to `AuthorCollection`, which now formally implements
  `collections.abc.Collection`.
* Added a `fullcredit build` command to generate a formatted contributor list from
  git history and an author database.
* Added a `fullcredit build` subcommand to format an author database as a
  credits list.

### Fixes

- Fixed infinite recursion when calling `len()` on an `AuthorCollection`.
