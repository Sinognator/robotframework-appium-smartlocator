# robotframework-appium-smartlocator

Smart locator resolver for Appium and Robot Framework.

---

## Overview

This library resolves mobile elements from human-readable descriptions and automatically generates the best locator strategy based on the current Appium page source.

It is designed primarily for Android mobile automation using Appium and Robot Framework.

---

## Features

- Human-readable element description (e.g. "botao continuar")
- Semantic parsing of element type and identifier
- Intelligent candidate scoring based on XML attributes
- Automatic locator generation (id, accessibility, UIAutomator, XPath)
- Seamless integration with Robot Framework
- Works with Appium mobile automation

---

## Installation

### From PyPI (future)

```bash
pip install robotframework-appium-smartlocator
```

### Local development

```bash
pip install -e .
```

---

## Project Structure

```text
robotframework-appium-smartlocator/
├── appium_smartlocator/
│   ├── __init__.py
│   ├── semantic_parser.py
│   ├── element_resolver.py
│   ├── locator_builder.py
│   ├── smart_element_resolver.py
│   └── smart_robot_library.py
├── pyproject.toml
└── README.md
```

---

## Usage in Robot Framework

### Import the library

```robot
*** Settings ***
Library    appium_smartlocator.SmartMobileLibrary
```

---

## Available Keywords

- `Resolver Locator Inteligente`
- `Clicar No Elemento`
- `Preencher Elemento`
- `Validar Elemento`

---

## Basic Example

```robot
*** Settings ***
Library    appium_smartlocator.SmartMobileLibrary

*** Test Cases ***
Validate Button
    Validar Elemento    botao continuar
```

---

## Example: Login Flow

```robot
*** Settings ***
Library    appium_smartlocator.SmartMobileLibrary

*** Test Cases ***
Login Example
    Preencher Elemento    campo usuario    meu_usuario
    Preencher Elemento    campo senha      minha_senha
    Clicar No Elemento    botao entrar
```

---

## How It Works

1. The library parses a human-readable description
2. Identifies element type and target text
3. Scans the Appium XML page source
4. Scores possible candidates
5. Selects the best match
6. Builds an optimized locator

---

## Locator Priority

The library generates locators in this order:

1. `resource-id` (best)
2. `accessibility id`
3. `UiSelector (Android)`
4. `XPath`
5. fallback (`//*`)

---

## Requirements

- Python 3.10+
- Robot Framework
- Appium
- Android device/emulator
- Appium page source available via driver

---

## Development Status

Current version: `0.1.0`

This is the first functional version of the library.

Planned improvements:

- Smarter fallback strategies
- Better scoring logic
- Improved logging/debugging
- Support for more complex layouts
- Possible iOS support in future

---

## Author

Paulo Rocha
