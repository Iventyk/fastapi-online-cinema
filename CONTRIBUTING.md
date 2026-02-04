## Git Workflow

This document describes a **safe and predictable Git workflow** for a team project where:

- `main` — stable branch (production / releases)
- `develop` — main development branch
- each task is implemented in a **separate feature branch**

The goal is to **minimize merge conflicts**, avoid losing changes, and keep the commit history clean and readable.

---

## 0. General Rules

- ❌ **NEVER push directly to** `develop` **or** `main`
- ✅ All work must be done via **feature branches** (each developer creates their own branch)
- ✅ Before any `pull`, `merge`, or `rebase`, the working tree **must be clean** (no uncommitted changes)
- ✅ All changes are merged into the repository **only via Pull Requests**

---

## 1. First Time: Cloning the Repository

Clone the repository as usual. Then switch to `develop` and update it:

```bash
git checkout develop
git pull origin develop
```

After this, always start new work from the updated develop branch.

## 2. Starting a New Task (Feature)

#### 2.1 Update develop

```bash
git checkout develop
git pull origin develop
```

#### 2.2 Create a Feature Branch

Branch names should clearly describe the work being done:

```bash
git checkout -b feature/user-authentication
```

Recommended branch name format:

- `feature/...` — new functionality  
- `fix/...` — bug fixes  
- `refactor/...` — refactoring  

## 3. Working in a Feature Branch

#### 3.1 Write your code. 

#### 3.2 Code Quality Checks & Running Tests before commit

Before committing your changes, make sure your code passes **formatting, linting, type checking, and tests**. This helps keep the project clean and maintainable.

#### Formatting with Black

```bash
poetry run black --check .  # checking
```

```bash
poetry run black .  # formatting
```

#### Linting with Flake8

```bash
poetry run flake8
```

#### Type Checking with mypy

```bash
poetry run mypy .
```

#### Running Tests

```bash
poetry run pytest
```

#### Running Tests with Coverage

```bash
poetry run pytest --cov=./ --cov-report=xml
```
#### 3.3 Check the status, add needed files and make commits when needed:

```bash
git status
git add .
```

#### 3.4 Commits

A commit = a logically complete piece of work. Commit messages should:

- be in English  
- start with lowercase  
- use past tense  
- include a prefix like `fix:`, `feat:`, etc.  

Common prefixes:

- `fix:` — bug fixes  
- `feat:` — new feature  
- `refactor:` — code changes without behavior change  
- `chore:` — technical or maintenance changes  
- `test:` — tests  
- `docs:` — documentation  

Examples:

```bash
git commit -m "feat: implemented jwt authentication"
```

## 4. Finishing Work on a Feature

#### 4.1 Updating Dependencies (if needed)

Since we are using Poetry for dependency management, add new packages with:

```bash
poetry add <package-name>
```

Then commit the updated `pyproject.toml` and `poetry.lock`:

```bash
git add pyproject.toml poetry.lock
git commit -m "chore: added <package-name> dependency"
```

⚠️ IMPORTANT: do NOT push yet !

## 5. Syncing with `develop` (MANDATORY)

This step helps you:  
- see conflicts **locally**  
- avoid breaking the `develop` branch

#### 5.1 Ensure a Clean Working Tree

```bash
git status
```

You should see:

```
nothing to commit, working tree clean
```

#### 5.2 Update develop

```bash
git checkout develop
git pull origin develop
```

#### 5.3 Merge develop into Your Feature Branch

Instead of rebase, we use merge to simplify handling multiple local commits:

```bash
git checkout your-branch
git merge develop
```

#### 5.4 Resolving Conflicts (if any)

Resolve conflicts in the affected files. Stage the resolved files:

```bash
git add .
```

Continue the merge (if necessary):

```bash
git commit -m "..."
```

If something goes wrong and you want to abort the merge:

```bash
git merge --abort
```

Don't hesitate to ask colleagues if you're unsure about conflict resolution.

## 6. Push to GitHub

After a successful merge:

```bash
git push origin your-branch
```

## 7. Pull Request

1. Open GitHub  
2. Create a **Pull Request**:  
   - **from:** `your-branch`  
   - **to:** `develop`  
3. Add a description:  
   - what has been done  
   - what reviewers should focus on  
4. Wait for test  
5. Wait for reviews
6. After approval — merge the PR

## 8. After Merge

Switch back to `develop` and update it:

```bash
git checkout develop
git pull origin develop
```

---

## Quick Workflow Summary

```
update develop
   ↓
create & switch to feature branch
   ↓
write code + commits
   ↓
update develop
   ↓
merge develop into feature branch
   ↓
resolve conflicts & commit (if any) 
   ↓
push feature branch
   ↓
create pull request → develop
```
