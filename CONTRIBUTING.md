# Contributing to OpenSTRAN

All contributions are welcome and done on a voluntary basis. If you are interested in contributing, continue reading to get set up with a standard development environment and understand this repositories best practices and guidelines.

## Requirements

* Python 3.14 or higher
* Docker

## Getting set up

### Using the devcontainer

Open the repository in VS Code and choose **Reopen in Container**. The
`.devcontainer/post-create.sh` script runs automatically and will:

1. Upgrade `pip`.
2. Create a virtual environment at `.venv/`.
3. Install OpenSTRAN in editable mode along with its development dependencies.
4. Register the virtual environment so it is active in every new terminal.

When it finishes, `pytest` works with no further setup.

### Manual setup

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

## Dependencies

| File | Installs | Use it when |
| --- | --- | --- |
| `requirements.txt` | OpenSTRAN + numpy + scipy | You just want to *run* OpenSTRAN |
| `requirements-dev.txt` | The above (editable) + pytest | You want to *develop* OpenSTRAN |

### Adding a dependency

Add it to the right place in `pyproject.toml`:

| The dependency is: | Goes in |
| --- | --- |
| Needed at runtime | `[project.dependencies]` |
| Needed only to run tests | `[project.optional-dependencies]` -> `dev` |
| Needed only to build docs | `[project.optional-dependencies]` -> `docs` |

## Running tests

```bash
pytest
```

The test suite configuration file is located  in `[tool.pytest.ini_options]` in `pyproject.toml`. The suite is parametrized and validates solver output against over 1,900 closed-form solutions, so it takes a little while to run.

The same command runs in CI on every push and pull request via
`.github/workflows/tests.yml`.

<b>Ensure all tests pass before opening a pull request.</b>

## Branching

OpenSTRAN uses two main branches. Contributions target `development`, and `main` holds released code.

| Branch | Purpose |
| --- | --- |
| `development` | For all development and contributions. Branch from here and open every pull request against it. |
| `main` | Released code. Updated only when `development` is promoted for a new release. |

Create your branch off `development` and name it `username/type/description`, where `type` is one of the commit prefixes described in the next section. Here is a quickstart example for how to create a new feature branch with development as the origin

```bash
git fetch -a
git switch development
git pull
git checkout -b <username>/feat/my-new-awesome-feature development
```

<b>GitHub pre-selects `main` as the base branch. Change the base to `development` before you open the pull request.</b>

A pull request left pointing at `main` will contain every commit that separates the two branches rather than just your work, which makes it difficult to review.

## Commit messages

Prefix every commit subject with one of the following six words followed by a colon. The same six words are used for the `type` segment of a branch name.

| Prefix | Use for |
| --- | --- |
| `feat:` | A new capability |
| `fix:` | A bug fix |
| `docs:` | Documentation only |
| `test:` | Tests only |
| `refactor:` | Restructuring with no change in behavior |
| `chore:` | Tooling, dependencies and CI |

Write the subject in the imperative mood and keep it under roughly 72 characters.

```
feat: closed form moment and shear determination
fix: correct shear envelope for loads applied at a support
test: parametrize simple span beam subject to point load
```

This convention takes effect with this document (09/07/2026), so commits made before this date predate the rule and do not conform.

## Pull requests

A pull request should meet the following at a minimum.

1. The base branch is set to `development`.
2. The full test suite passes locally.
3. New or changed behavior is covered by a test if applicable (use your judgement).
4. The description links a related issue with `Closes #12`, or explains why no issue exists.
5. The description endeavors to describe what changed and why.
6. Docstrings are updated for any change to the public API. Docstrings follow the napoleon format used throughout `src/OpenSTRAN`.

Opening the pull request loads a template containing this checklist. Keep the pull request focused on a single concern; several small pull requests are easier to review than one large one.

## Reporting issues

Bug reports and feature requests both use a form that prompts for the information needed to act on them. Reporting a bug you have found, or sharing your experience with the library are welcome contributions.

Because OpenSTRAN is a solver, a bug report is only actionable when it includes a minimal model that can be run as written, together with the result you expected and the result you obtained. `quickstart_example.py` is a good starting point to adapt.

## Building the documentation

```bash
pip install -e ".[docs]"
cd docs && make html
```

Output is located in `docs/build/html`.