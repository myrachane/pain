<div align="center">
  <img src="https://github.com/user-attachments/assets/3c9e311d-b2dd-4338-ae5a-6c1d10bacd41" alt="PAIN Logo">
</div>
<p align="center">
  $$\color{yellow}{\large \textsf{Because setting up C++ projects shouldn’t hurt this much!}}$$
</p>



<hr>

<h4 align="center">
  <a href="#installation">Install</a>
  ·
  <a href="COMMANDS.md">Commands</a>
  ·
  <a href="ARCHITECTURE.md">Architecture</a>
</h4>

<div align="center">
  <a href="https://github.com/omnimistic/pain/releases/latest">
    <img alt="Latest release" src="https://img.shields.io/github/v/release/omnimistic/pain?style=for-the-badge&color=C9CBFF&logoColor=D9E0EE&labelColor=302D41&label=PAIN&include_prerelease&sort=semver" />
  </a>
  <a href="https://github.com/omnimistic/pain/pulse">
    <img alt="Last commit" src="https://img.shields.io/github/last-commit/omnimistic/pain?style=for-the-badge&color=8bd5ca&logoColor=D9E0EE&labelColor=302D41"/>
  </a>
  <a href="https://github.com/omnimistic/pain/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/omnimistic/pain?style=for-the-badge&color=ee999f&logoColor=D9E0EE&labelColor=302D41" />
  </a>
  <a href="https://python.org">
    <img alt="Python" src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&color=c69ff5&logoColor=D9E0EE&labelColor=302D41" />
  </a>
  <a href="https://github.com/omnimistic/pain/stargazers">
    <img alt="Stars" src="https://img.shields.io/github/stars/omnimistic/pain?style=for-the-badge&color=f9e2af&logoColor=D9E0EE&labelColor=302D41" />
  </a>
</div>

**PAIN** is a zero-configuration C++ scaffolding engine and dependency auto-linker powered by `vcpkg`.

Rather than forcing you to choose between spending hours writing CMake scripts or battling global environment variables, PAIN offers the best of both worlds — the portability of a standard CMake build, along with the convenience of automated, surgical dependency injection.

> [!CAUTION]
> **Built because C++ package management was still stuck in the stone age.**

## Installation

### Windows
Download the pre-compiled `pain.exe` from the [latest release](https://github.com/omnimistic/pain/releases/latest) and add it to your system PATH.

### Linux & macOS (Build from Source)
You can compile it into a native binary for your system using [PyInstaller](https://www.pyinstaller.org/).

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Compile to a single executable:
   ```bash
   # Navigate to the repo root
   pyinstaller --onefile pain.py
   ```

3. Move the binary to your PATH:
   ```bash
   # Move the resulting binary from the 'dist' folder
   sudo mv dist/pain/usr/local/bin/
   ```

## Quick Start

Once installed, you can manage your C++ projects with ease:

```bash
# Initialize a new C++ project
pain init my_app
cd my_app

# Add a library
pain add fmt

# Build and run the project
pain build
pain run
```

## Features

- Transform C++ package management into a single-command experience.
- Easily manage dependencies with automated `vcpkg.json` mutation.
- Blazingly fast global binary caching (compile once, link instantly anywhere).
- Sane default settings for modern CMake (C++20).
- Regex-powered Auto-Linker that writes your `target_link_libraries` for you.

## Requirements

- Git >= **2.19.0**
- CMake >= **3.21**
- A **C++** Compiler (GCC, Clang, or MSVC)
- vcpkg (PAIN will install a copy using git)

---

## License & Attribution

This project is licensed under the **GPL-3.0 License**.

> [!IMPORTANT]  
> If you redistribute or modify PAIN, or incorporate PAIN (or any part of it) into your own projects, you must retain the original author credits and provide a link back to this repository:  
> PAIN repository: https://github.com/omnimistic/pain/  
> Original author (me): [@omnimistic](https://github.com/omnimistic)

---

<p align="center">
  $\color{#D30000}{\large \textsf{Built with pure, unadulterated hatred for C++ linker errors.}}$
</p>
