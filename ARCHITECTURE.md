# PAIN Architecture Overview

PAIN is a single-file Python CLI (`pain.py`) that acts as a thin orchestration layer over two well-established tools: **vcpkg** (Microsoft's C++ package manager) and **CMake**. It doesn't replace either — it automates the tedious glue work between them so you can go from zero to a working C++ project in seconds.

---

## The Two-Layer Model

PAIN operates across two scopes:

- **Global cache** — a single vcpkg installation at `~/.pain/vcpkg/`, shared across all your projects. Libraries are downloaded and compiled once here.
- **Project scope** — per-project files (`vcpkg.json`, `.pain_deps.cmake`) that declare which libraries from the cache a given project actually uses.

This means installing a library is a one-time cost. Adding it to a new project is instant.

---

## Core Files

| File | Purpose |
|---|---|
| `CMakeLists.txt` | Standard CMake build definition. PAIN injects a single hook line into this. |
| `vcpkg.json` | vcpkg manifest. Declares the project's dependencies by name. |
| `CMakePresets.json` | Points CMake at the vcpkg toolchain file so it can find packages. |
| `.pain_deps.cmake` | Auto-generated sidecar. Contains the `find_package()` and `target_link_libraries()` calls for each linked library. |

---

## How Dependencies Flow

```
pain install <lib>
    └── vcpkg compiles the library into ~/.pain/vcpkg/packages/

pain add <lib>
    ├── Adds <lib> to vcpkg.json (manifest)
    └── Extracts CMake hooks → appends to .pain_deps.cmake

pain build
    ├── CMake reads CMakeLists.txt
    ├── PAIN hook: `include(.pain_deps.cmake OPTIONAL)` pulls in all find_package() calls
    └── vcpkg toolchain resolves package paths from the global cache
```

---

## The PAIN Hook

The key piece of magic is a single line injected into `CMakeLists.txt` after the `project()` declaration:

```cmake
include(.pain_deps.cmake OPTIONAL)
```

This defers all dependency wiring to the sidecar file. CMakeLists.txt stays clean and human-readable; PAIN manages `.pain_deps.cmake` automatically. The `OPTIONAL` keyword means the project still configures correctly even if no libraries have been added yet.

---

## CMake Hook Extraction

When you run `pain add <lib>`, PAIN needs to know the correct `find_package()` and `target_link_libraries()` calls for that library. It tries three strategies in order:

1. **vcpkg install output** — vcpkg often prints a usage block when a package is installed.
2. **Usage file** — vcpkg ships a static `usage` file in the package's share directory for many ports.
3. **Config file synthesis** — if neither of the above yields results (common on MinGW), PAIN parses the package's `*-config.cmake` and `*-targets.cmake` files directly to infer the correct CMake target names.

---

## Platform Handling

PAIN detects the host OS and available compiler at runtime to select the right vcpkg triplet (e.g. `x64-linux`, `x64-windows`, `arm64-osx`, `x64-mingw-dynamic`). This triplet is set as an environment variable and passed through to CMake so vcpkg resolves the correct pre-compiled binaries for your platform. On MinGW specifically, PAIN also forces the `MinGW Makefiles` generator to prevent CMake from accidentally falling back to NMake.

---

## Project Lifecycle

```
pain doctor       -> installs vcpkg globally, configures environment
pain init         -> scaffolds project files including the CMake hook
pain adopt        -> injects the hook into an existing CMake project
pain install      -> compiles a library into the global cache
pain add          -> wires a cached library into the current project
pain build        -> runs cmake configure + build
pain run          -> finds and executes the compiled binary
```

`pain sync` is available to rebuild the sidecar from scratch if `.pain_deps.cmake` gets out of sync with `vcpkg.json` for wahtever reason(probably because u manually touched either or both of those files)
