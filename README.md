<div align="center">
  <img src="https://github.com/user-attachments/assets/3c9e311d-b2dd-4338-ae5a-6c1d10bacd41" alt="PAIN Logo">
</div>

<hr>

<h4 align="center">
  <a href="#getting-started">Install</a>
  ·
  <a href="COMMANDS.md">Commands</a>
  ·
  <a href="ARCHITECTURE.md">Architecture</a>
</h4>

<div align="center"><p>
    <a href="https://github.com/omnimistic/pain/releases/latest">
      <img alt="Latest release" src="https://img.shields.io/github/v/release/omnimistic/pain?style=for-the-badge&color=C9CBFF&logoColor=D9E0EE&labelColor=302D41&include_prerelease&sort=semver" />
    </a>
    <a href="https://github.com/yourusername/pain/pulse">
      <img alt="Last commit" src="https://img.shields.io/github/last-commit/omnimistic/pain?style=for-the-badge&color=8bd5ca&logoColor=D9E0EE&labelColor=302D41"/>
    </a>
    <a href="https://python.org">
      <img alt="Python" src="https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&color=c69ff5&logoColor=D9E0EE&labelColor=302D41" />
    </a>
    <a href="https://github.com/yourusername/pain/blob/main/LICENSE">
      <img alt="License" src="https://img.shields.io/github/license/omnimistic/pain?style=for-the-badge&color=ee999f&logoColor=D9E0EE&labelColor=302D41" />
    </a>
    <a href="https://github.com/yourusername/pain/issues">
      <img alt="Issues" src="https://img.shields.io/github/issues/omnimistic/pain?style=for-the-badge&color=F5E0DC&logoColor=D9E0EE&labelColor=302D41" />
    </a>
</div>

**PAIN** is a zero-configuration C++ scaffolding engine and dependency auto-linker powered by `vcpkg`. 
Rather than forcing you to choose between spending hours writing CMake scripts or battling global environment variables, PAIN offers the best of both worlds—the portability of a standard CMake build, along with the convenience of automated, surgical dependency injection.

> [!CAUTION]
> **Built because C++ package management was still stuck in the stone age.**

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
