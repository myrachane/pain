## System Commands

### `pain doctor`
Performs a full system diagnostic and environment configuration.

- **Verification**: Checks for Git, CMake, and a valid C++ compiler.
- **Bootstrapping**: Clones and compiles a global vcpkg instance in `~/.pain/`.
- **Environment**: Idempotently configures `VCPKG_ROOT` and system PATH in shell profiles.

**Usage:**
```bash
pain doctor
```

---

## Project Setup

### `pain init <name>`
Scaffolds a brand-new, modern C++ project environment.

- **Files**: Generates `src/main.cpp`, `vcpkg.json`, and `CMakePresets.json`.
- **Configuration**: Sets C++20 standards and injects the PAIN auto-linker hook.

**Usage:**
```bash
pain init MyProject
```

### `pain adopt`
Injects PAIN capabilities into an existing CMake-based project.

- **Discovery**: Recursively searches parent directories for a `CMakeLists.txt`.
- **Injection**: Safely inserts the auto-linker hook after the `project()` declaration.

**Usage:**
```bash
pain adopt
```

---

## Dependency Management

### `pain search <query>`
Queries the local vcpkg registry for available C++ libraries.

- **Mechanism**: Searches the local offline catalog for high-speed results.

**Usage:**
```bash
pain search sqlite3
```

### `pain install <lib>`
Downloads and compiles a library into the global PAIN binary cache.

- **UX**: Streams live compilation output to the terminal.
- **Caching**: Compiled binaries are stored in `~/.pain/vcpkg/packages` for instant re-use.

**Usage:**
```bash
pain install sfml
```

### `pain uninstall <lib>`
Permanently removes a library from the global PAIN binary cache.

- **Cleanup**: Purges compiled files from the global storage to free up disk space.

**Usage:**
```bash
pain uninstall sfml
```

### `pain add <lib>`
Links an installed library to the current project environment.

- **Manifest**: Appends the library to the project's `vcpkg.json` dependencies.
- **Sidecar**: Extracts CMake usage hooks and writes them to `.pain_deps.cmake`.

**Usage:**
```bash
pain add fmt
```

### `pain remove <lib>`
De-links a library from the current project.

- **Removal**: Updates the manifest and surgically removes the library's hooks from the sidecar.

**Usage:**
```bash
pain remove fmt
```

### `pain sync`
Regenerates the dependency sidecar based on the current manifest.

- **Repair**: Audits `vcpkg.json` and rebuilds `.pain_deps.cmake` from scratch.

**Usage:**
```bash
pain sync
```

### `pain list`
Displays a detailed list of C++ libraries.

- **Context**: Lists project-specific links if run inside a project, otherwise shows the global cache.

**Usage:**
```bash
pain list
```

---

## Execution Engine

### `pain build`
Automates the CMake configuration and compilation process.

- Runs `cmake -B build` followed by `cmake --build build`.

**Usage:**
```bash
pain build
```

### `pain run`
Locates and executes the compiled project binary.

- Automatically finds the executable inside the `build/` directory across platforms.

**Usage:**
```bash
pain run
```

### `pain clean`
Safely removes the local build environment.

- Deletes the `build/` directory for a clean re-configuration.

**Usage:**
```bash
pain clean
```

---

<p align="center">
  <strong>Built to end the era of manually editing CMake files.</strong>
</p>
