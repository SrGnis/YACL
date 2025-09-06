# Contributing to YACL

Thank you for your interest in contributing to **YACL**! This guide will walk you through setting up your environment, understanding the project’s structure, and contributing effectively.

---

## Getting Started

Before diving in, make sure you have **Python 3.11.9** ( other versions should work as well but we focus on 3.11.9 for now ) and **Git** installed, along with some basic familiarity with Python.

To begin, fork the repository on GitHub and clone your fork locally:

```bash
git clone https://github.com/your-username/yacl.git
cd yacl
git submodule update --init --recursive  # for Azure-ttk-theme
```

We recommend using **pyenv** to install and manage Python 3.11.9. Once installed, create and activate a virtual environment:

```bash
pyenv install 3.11.9
pyenv shell 3.11.9

python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

With your environment active, install dependencies and the package itself in editable mode:

```bash
pip install -r requirements.txt
pip install -e .
```

To confirm that everything works, run:

```bash
yacl
```

---

## Development Guidelines

### Code Style and Patterns

YACL follows a architecture inspired by the MVC (Model-View-Controller) pattern. Always use type hints when possible and keep business logic, data, and UI responsibilities separated.

* **Models** define data structures.
* **Model Managers** handle operations on models.
* **Views** are responsible for UI components and layouts.
* **Controllers** connect Views with Model Managers.
* **Services** provide reusable application functionality such as settings, paths, and event handling.
* **UI** contains application-specific interface code like the main window and widgets.
* **Utils** house helper functions.

When in doubt, prefer clarity and separation of concerns. Communication between components should generally happen through the **event system**, and core functionality should live in **services** so it can be reused.


## I Want to Do X, What Should I Change?

To help you navigate YACL’s architecture, here are some common scenarios and where to make changes:

* **Modify the UI**
  * **Views**: define layouts and how things are arranged
  * **UI**: implement widgets and window-specific code

* **Change how data is stored or represented**
  - Modify the **Models**. If you need logic for creating, updating, or deleting data, put it in a **Model Manager** rather than the model itself.

* **Implement new business logic (rules, workflows, data handling)**
  - Extend or create a **Controller**. Controllers bridge between the user interface and the model layer.

* **Add reusable functionality (e.g., settings, file handling, event dispatching)**
  - Create or extend a **Service**. Services are designed to be shared across different parts of the app.

* **Write helper functions that don’t belong to a single component**
  - Place them in **Utils**, but only if they’re truly general-purpose. Otherwise, keep them within the most relevant component.

* **Introduce cross-component communication**
  - Prefer using the **event system** instead of direct calls. This keeps components decoupled.

---

## Making Contributions

### Workflow

1. Start by looking for an open issue or creating a new one. If you want to work on it, leave a comment so others know it’s taken.

2. Create a new branch from `main` using a descriptive name:

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. Write your code following existing patterns.

4. Once your changes are ready, commit with a meaningful message. We use the **conventional commit format** (e.g., `feat: add new widget for settings`).

5. Push your branch and open a pull request. Be sure to describe your changes clearly, reference related issues, and include screenshots for UI changes.

### Commit Messages

We use the following prefixes to keep commit history readable:

* **feat:** new features
* **fix:** bug fixes
* **docs:** documentation updates
* **test:** new or updated tests
* **refactor:** restructuring code without changing behavior
* **style:** formatting-only changes

---
