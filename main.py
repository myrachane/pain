import os
import sys
import subprocess
import re
import json
import shutil
import threading
import time
from pathlib import Path


# CONSTANTS

# ANSI color codes for terminal output
C_RED = "\033[91m"
C_TERRACOTTA = "\033[38;5;173m"
C_YELLOW = "\033[93m"
C_GREEN = "\033[92m"
C_RESET = "\033[0m"

# Status indicators
STATUS_OK = f"{C_GREEN}[OK]{C_RESET}"
STATUS_FAIL = f"{C_RED}[FAIL]{C_RESET}"
STATUS_INFO = f"{C_TERRACOTTA}[INFO]{C_RESET}"

# Global paths
PAIN_DIR = Path.home() / ".pain"
GLOBAL_VCPKG_PATH = PAIN_DIR / "vcpkg"

# Single source of truth for the PAIN hook line
PAIN_HOOK_LINE = "include(.pain_deps.cmake OPTIONAL)"
PAIN_HOOK_BLOCK = f"# --- PAIN Auto-Linker Hook ---\n{PAIN_HOOK_LINE}"

# Regex for verifying a package is installed (handles triplet suffixes like fmt:x64-linux)
def _vcpkg_installed_pattern(lib_name: str) -> re.Pattern:
    return re.compile(rf'^{re.escape(lib_name)}(?::[\w-]+)?\s+', re.MULTILINE)


# HELPER FUNCTIONS

class Throbber:
    def __init__(self, message="Working..."):
        self.throbber_chars = ['|', '/', '-', '\\']
        self.delay = 0.1
        self.running = False
        self.message = message
        self.thread = None

    def spin(self):
        i = 0
        while self.running:
            char = self.throbber_chars[i % len(self.throbber_chars)]
            sys.stdout.write(f'\r  {C_YELLOW}{char}{C_RESET} {self.message}')
            sys.stdout.flush()
            time.sleep(self.delay)
            i += 1

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.spin)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()
            self.thread = None  # Reset so the instance can be safely reused
        # Clears the line safely using a generous padding of spaces
        sys.stdout.write('\r' + ' ' * 80 + '\r')
        sys.stdout.flush()


def fatal(msg: str) -> None:
    # Print error message and exit the program
    print(f"\n{STATUS_FAIL} Error: {msg}\n")
    sys.exit(1)


def generate_manifest(root_path: Path, project_name: str) -> bool:
    # Create vcpkg.json manifest if it doesn't already exist
    manifest_path = root_path / "vcpkg.json"
    if manifest_path.exists():
        print(f"  {STATUS_INFO} vcpkg.json already exists, skipping.")
        return False

    safe_name = project_name.replace('_', '-').lower()
    manifest = {
        "name": safe_name,
        "version": "0.1.0",
        "dependencies": []
    }

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding='utf-8')
    print(f"  {STATUS_INFO} Created vcpkg.json manifest.")
    return True


def generate_presets(root_path: Path) -> bool:
    # Generate CMakePresets.json to integrate with global vcpkg installation
    presets_path = root_path / "CMakePresets.json"
    if presets_path.exists():
        print(f"  {STATUS_INFO} CMakePresets.json already exists, skipping.")
        return False

    presets = {
        "version": 3,
        "configurePresets": [{
            "name": "vcpkg",
            "displayName": "PAIN vcpkg Toolchain",
            "binaryDir": "${sourceDir}/build",
            "cacheVariables": {
                "CMAKE_TOOLCHAIN_FILE": str(
                    GLOBAL_VCPKG_PATH / "scripts" / "buildsystems" / "vcpkg.cmake"
                ).replace('\\', '/')
            }
        }]
    }

    presets_path.write_text(json.dumps(presets, indent=2) + "\n", encoding='utf-8')
    print(f"  {STATUS_INFO} Created CMakePresets.json for IDE integration.")
    return True


def inject_hook(cmake_path: Path) -> bool:
    # Inject PAIN dependency hook into CMakeLists.txt after the project() declaration
    content = cmake_path.read_text(encoding='utf-8')

    if PAIN_HOOK_LINE in content:
        print(f"  {STATUS_INFO} PAIN hook already present in CMakeLists.txt, skipping.")
        return False

    # Insert hook after the project() call using a lambda to safely handle newlines.
    # re.DOTALL allows matching multiline project() declarations.
    new_content, count = re.subn(
        r'(project\s*\(.*?\))',
        lambda m: m.group(1) + f'\n\n{PAIN_HOOK_BLOCK}\n',
        content,
        flags=re.IGNORECASE | re.DOTALL
    )

    if count == 0:
        raise RuntimeError("Could not find a 'project()' declaration in CMakeLists.txt.")

    # Guard against multiple project() declarations to avoid injecting the hook more than once
    if count > 1:
        raise RuntimeError("Multiple 'project()' declarations found; cannot safely inject hook.")

    cmake_path.write_text(new_content, encoding='utf-8')
    print(f"  {STATUS_INFO} Injected PAIN hook into CMakeLists.txt.")
    return True


def check_tool(name: str, command: list) -> bool:
    # Check if a required command-line tool is available and executes successfully
    try:
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            print(f"  {STATUS_OK} {name} is installed and available in PATH.")
            return True
        else:
            print(f"  {STATUS_FAIL} {name} returned a non-zero exit code.")
            return False
    except FileNotFoundError:
        print(f"  {STATUS_FAIL} {name} is missing or not in PATH.")
        return False


def setup_global_paths() -> None:
    # Configure VCPKG_ROOT environment variable and add vcpkg to PATH
    print(f"\n{STATUS_INFO} Configuring environment variables...")

    vcpkg_str = str(GLOBAL_VCPKG_PATH)

    # Initialize with safe defaults to prevent UnboundLocalError if branches ever change
    target_profile = None
    export_lines = None
    source_cmd = None

    try:
        if os.name == 'nt':
            subprocess.run(['setx', 'VCPKG_ROOT', vcpkg_str], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            print(f"  {STATUS_OK} VCPKG_ROOT environment variable set.")
            print(f"  {C_YELLOW}Note: Restart your terminal for changes to take effect.{C_RESET}")
            return
        else:
            shell_path = os.environ.get("SHELL", "")
            shell_name = Path(shell_path).name.lower()
            home = Path.home()

            if shell_name == "fish":
                target_profile = home / ".config" / "fish" / "config.fish"
                export_lines = f'\n# BEGIN PAIN\nset -gx VCPKG_ROOT "{vcpkg_str}"\nfish_add_path "{vcpkg_str}"\n# END PAIN\n'
                source_cmd = f"source {target_profile}"

            elif shell_name in ["tcsh", "csh"]:
                target_profile = home / f".{shell_name}rc"
                export_lines = f'\n# BEGIN PAIN\nsetenv VCPKG_ROOT "{vcpkg_str}"\nsetenv PATH "$VCPKG_ROOT:$PATH"\n# END PAIN\n'
                source_cmd = f"source {target_profile}"

            elif shell_name == "zsh":
                target_profile = home / ".zshrc"
                export_lines = f'\n# BEGIN PAIN\nexport VCPKG_ROOT="{vcpkg_str}"\nexport PATH="$VCPKG_ROOT:$PATH"\n# END PAIN\n'
                source_cmd = f"source {target_profile}"

            elif shell_name == "bash":
                # macOS bash login shells read .bash_profile, not .bashrc
                target_profile = (home / ".bash_profile") if sys.platform == 'darwin' else (home / ".bashrc")
                export_lines = f'\n# BEGIN PAIN\nexport VCPKG_ROOT="{vcpkg_str}"\nexport PATH="$VCPKG_ROOT:$PATH"\n# END PAIN\n'
                source_cmd = f"source {target_profile}"

            else:
                # Fallback to POSIX .profile
                target_profile = home / ".profile"
                export_lines = f'\n# BEGIN PAIN\nexport VCPKG_ROOT="{vcpkg_str}"\nexport PATH="$VCPKG_ROOT:$PATH"\n# END PAIN\n'
                source_cmd = f". {target_profile}"

            if target_profile is None:
                print(f"  {STATUS_FAIL} Could not determine shell profile path.")
                return

            target_profile.touch(exist_ok=True)
            content = target_profile.read_text(encoding='utf-8')

            # Ensure strict idempotency for the entire block
            if "# BEGIN PAIN" not in content:
                target_profile.write_text(content + export_lines, encoding='utf-8')
                print(f"  {STATUS_OK} Added PAIN environment paths to shell profile ({target_profile.name}).")
                print(f"  {C_YELLOW}Run '{source_cmd}' or restart your terminal.{C_RESET}")
            else:
                print(f"  {STATUS_INFO} PAIN environment paths already configured in {target_profile.name}.")

    except Exception as e:
        print(f"  {STATUS_FAIL} Failed to configure environment variables: {e}")


def _extract_cmake_usage_lines(vcpkg_output: str, lib_name: str) -> list[str]:
    # only captures lines from within the
    # "provides CMake targets:" usage block, not the entire vcpkg output
    # This prevents false positives from dependency resolution messages
    usage_lines = []
    capturing = False

    for line in vcpkg_output.split('\n'):
        if "provides CMake targets:" in line:
            capturing = True
            continue

        if capturing:
            stripped = line.strip()

            # An empty line signals the end of the usage block
            if not stripped:
                break

            if stripped.startswith("find_package(") or stripped.startswith("target_link_libraries("):
                # Dynamically replace the placeholder target with ${PROJECT_NAME}
                if stripped.startswith("target_link_libraries("):
                    stripped = re.sub(
                        r'target_link_libraries\([^ ]+',
                        'target_link_libraries(${PROJECT_NAME}',
                        stripped
                    )
                usage_lines.append(stripped)

    return usage_lines


# RUNNERS

def run_init(name: str) -> None:
    # Create a new C++ project with PAIN scaffolding
    if not re.match(r'^[a-zA-Z0-9_-]+$', name) or name.startswith(('-', '.')):
        fatal("Invalid project name. Use only letters, numbers, hyphens, and underscores.")

    root = Path.cwd() / name
    if root.exists():
        fatal(f"Directory '{name}' already exists.")

    print(f"\n{STATUS_INFO} Creating new project: '{name}'...")

    root.mkdir()
    (root / "src").mkdir()

    # Create main source file
    (root / "src" / "main.cpp").write_text(
        '#include <iostream>\n\n'
        'int main() {\n'
        '    std::cout << "Hello from PAIN v2.0!\\n";\n'
        '    return 0;\n'
        '}\n',
        encoding='utf-8'
    )

    cmake_content = (
        "cmake_minimum_required(VERSION 3.21)\n\n"
        f"project({name})\n\n"
        "set(CMAKE_CXX_STANDARD 20)\n"
        "set(CMAKE_CXX_STANDARD_REQUIRED ON)\n\n"
        f"add_executable({name} src/main.cpp)\n\n"
        f"{PAIN_HOOK_BLOCK}\n"
    )
    (root / "CMakeLists.txt").write_text(cmake_content, encoding='utf-8')

    # Create .gitignore
    (root / ".gitignore").write_text(
        "build/\n"
        "vcpkg_installed/\n"
        ".vscode/\n"
        ".vs/\n"
        "*.exe\n"
        ".pain_deps.cmake\n",
        encoding='utf-8'
    )

    generate_manifest(root, name)
    generate_presets(root)

    print(f"{STATUS_OK} Project '{name}' created successfully!\n")


def run_adopt() -> None:
    # Adopt an existing CMake project and make it PAIN-compatible
    curr = Path.cwd()
    root = None

    print(f"\n{STATUS_INFO} Searching for CMakeLists.txt...")

    # Capped search depth to 3 levels up to prevent adopting random root directories
    search_paths = [curr] + list(curr.parents)[:3]
    for parent in search_paths:
        if (parent / "CMakeLists.txt").exists():
            root = parent
            break

    if not root:
        fatal("No CMakeLists.txt found. Are you inside a CMake-based C++ project?")

    if root != curr:
        print(f"  {STATUS_INFO} Found project root above current directory: {root}")

    print(f"{STATUS_INFO} Adopting project at: {root}")

    cmake_content = (root / "CMakeLists.txt").read_text(encoding='utf-8')
    match = re.search(r'project\s*\(\s*([a-zA-Z0-9_-]+)', cmake_content, re.IGNORECASE | re.DOTALL)
    proj_name = match.group(1) if match else root.name

    try:
        inject_hook(root / "CMakeLists.txt")
    except RuntimeError as e:
        fatal(str(e))

    generate_manifest(root, proj_name)
    generate_presets(root)

    # Update .gitignore if it exists
    gitignore = root / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text(encoding='utf-8')
        if ".pain_deps.cmake" not in content:
            gitignore.write_text(content.rstrip() + "\n\n# PAIN\n.pain_deps.cmake\n", encoding='utf-8')

    print(f"{STATUS_OK} Project successfully adopted by PAIN!\n")


def run_doctor() -> None:
    # Perform system diagnostics and install/configure vcpkg if needed
    print(f"\n{STATUS_INFO} Running PAIN System Diagnostics...\n")

    tools_ok = True

    print(f"{STATUS_INFO} Checking build tools:")
    if not check_tool("Git", ["git", "--version"]):
        tools_ok = False
    if not check_tool("CMake", ["cmake", "--version"]):
        tools_ok = False

    # Check for C++ compiler — checked separately to avoid printing misleading FAIL
    # for MSVC when g++/clang++ is already found
    compiler_ok = False
    if check_tool("C++ Compiler (g++/clang++)", ["c++", "--version"]):
        compiler_ok = True
    elif check_tool("MSVC (cl.exe)", ["cl", "/?"]):
        compiler_ok = True

    if not compiler_ok:
        print(f"  {STATUS_FAIL} No C++ compiler detected. vcpkg bootstrap may fail.")
        tools_ok = False

    if not tools_ok:
        fatal("Missing required tools. Please install Git, CMake, and a C++ compiler.")

    print(f"\n{STATUS_INFO} Checking global vcpkg at: {GLOBAL_VCPKG_PATH}")

    vcpkg_exe = GLOBAL_VCPKG_PATH / ("vcpkg.exe" if os.name == 'nt' else "vcpkg")

    if GLOBAL_VCPKG_PATH.exists() and vcpkg_exe.exists():
        print(f"  {STATUS_OK} vcpkg is installed and ready.")
    else:
        print(f"  {STATUS_FAIL} vcpkg installation not found.")

        choice = input(f"\n  {C_YELLOW}Install vcpkg globally now? [Y/n]: {C_RESET}").strip().lower()

        if choice in ['y', 'yes', '']:
            print(f"\n  {STATUS_INFO} Bootstrapping vcpkg (this may take a few minutes)...")

            PAIN_DIR.mkdir(parents=True, exist_ok=True)

            try:
                if GLOBAL_VCPKG_PATH.exists():
                    shutil.rmtree(GLOBAL_VCPKG_PATH, ignore_errors=True)

                subprocess.run(
                    ["git", "clone", "https://github.com/microsoft/vcpkg.git", str(GLOBAL_VCPKG_PATH)],
                    check=True
                )

                bootstrap_script = "bootstrap-vcpkg.bat" if os.name == 'nt' else "./bootstrap-vcpkg.sh"
                subprocess.run([bootstrap_script, "-disableMetrics"], cwd=GLOBAL_VCPKG_PATH, check=True)

                print(f"  {STATUS_OK} vcpkg installed successfully!")
                setup_global_paths()

            except Exception as e:
                # Clean up any partial installation so doctor can offer a fresh retry next time
                if GLOBAL_VCPKG_PATH.exists():
                    shutil.rmtree(GLOBAL_VCPKG_PATH, ignore_errors=True)
                fatal(f"Failed to install vcpkg. Partial installation removed.\nDetails: {e}")
        else:
            print(f"  {STATUS_INFO} vcpkg installation skipped.")

    # Ensure cache directory exists
    (PAIN_DIR / "archives").mkdir(exist_ok=True)

    print(f"\n{STATUS_OK} PAIN diagnostics completed.\n")


def run_search(query: str) -> None:
    # Searches the local vcpkg registry for available packages
    print(f"\n{STATUS_INFO} Searching vcpkg registry for '{query}'...\n")

    vcpkg_exe = GLOBAL_VCPKG_PATH / ("vcpkg.exe" if os.name == 'nt' else "vcpkg")
    if not vcpkg_exe.exists():
        fatal("vcpkg is not installed. Run 'pain doctor' first to set up your environment.")

    throbber = Throbber(f"Fetching packages matching '{query}'...")
    throbber.start()

    try:
        result = subprocess.run(
            [str(vcpkg_exe), "search", query],
            capture_output=True,
            text=True
        )
        throbber.stop()
    except Exception as e:
        throbber.stop()
        fatal(f"Search failed during execution:\n{e}")

    if result.returncode != 0:
        if not result.stdout.strip():
            # No output at all — genuine vcpkg failure
            fatal(f"Search failed. vcpkg encountered an error:\n{result.stderr.strip()}")
        else:
            # Non-zero exit but there is output — vcpkg may still have returned results
            # (e.g. "no packages found" message). Fall through and let the output checks handle it.
            print(f"  {STATUS_INFO} vcpkg exited with code {result.returncode}, attempting to parse output anyway.")

    output = result.stdout.strip()

    if not output or "No packages match" in output:
        print(f"  {STATUS_FAIL} No libraries found matching '{query}'.")
        return

    lines = output.split('\n')
    for line in lines:
        if not line.strip() or line.startswith("If your library") or line.startswith("vcpkg search"):
            continue

        parts = line.split(maxsplit=1)
        name = parts[0]
        desc = parts[1] if len(parts) > 1 else ""

        if len(desc) > 80:
            desc = desc[:77] + "..."

        print(f"  {C_GREEN}{name.ljust(25)}{C_RESET} {desc}")

    print(f"\n{STATUS_OK} Search complete. Use {C_YELLOW}pain install <lib>{C_RESET} to download.\n")


def run_install(lib_name: str) -> None:
    # Downloads and compiles a library into the global cache
    print(f"\n{STATUS_INFO} Installing '{lib_name}' globally...")
    print(f"  {C_YELLOW}If this is your first time installing this library, it may take a few minutes to download and compile from source.{C_RESET}\n")

    vcpkg_exe = GLOBAL_VCPKG_PATH / ("vcpkg.exe" if os.name == 'nt' else "vcpkg")
    if not vcpkg_exe.exists():
        fatal("vcpkg is not installed. Run 'pain doctor' first to set up your environment.")

    try:
        # Use check=True so a non-zero vcpkg exit code raises immediately
        # with a CalledProcessError, rather than silently falling through to the
        # list-check and producing a misleading "not found in cache" error message
        subprocess.run([str(vcpkg_exe), "install", lib_name], check=True)

        # Secondary validation: confirm the library actually landed in the installed list.
        # This catches edge cases where vcpkg exits 0 but emits build warnings without
        # producing a usable package.
        list_check = subprocess.run([str(vcpkg_exe), "list", lib_name], capture_output=True, text=True)
        if not _vcpkg_installed_pattern(lib_name).search(list_check.stdout):
            fatal(
                f"Installation finished, but '{lib_name}' was not found in the global cache. "
                f"Check the output above for build errors."
            )

        print(f"\n{STATUS_OK} Successfully installed '{lib_name}' to the global cache.")
        print(f"  {C_YELLOW}Tip: You can now run 'pain add {lib_name}' in any project to link it instantly.{C_RESET}\n")

    except subprocess.CalledProcessError:
        # vcpkg already printed its own error output to the terminal since we didn't
        # capture stdout/stderr, so just provide a clean summary line.
        fatal(f"vcpkg failed to install '{lib_name}'. Check the output above for details.")
    except SystemExit:
        raise  # Let fatal()'s sys.exit() propagate normally
    except Exception as e:
        fatal(f"Unexpected error while installing '{lib_name}': {e}")


def run_add(lib_name: str) -> None:
    # Links a globally installed library to the current project
    curr = Path.cwd()
    manifest_path = curr / "vcpkg.json"
    sidecar_path = curr / ".pain_deps.cmake"

    if not (curr / "CMakeLists.txt").exists() or not manifest_path.exists():
        fatal("You must be inside a PAIN project (with a CMakeLists.txt and vcpkg.json) to run 'add'.")

    vcpkg_exe = GLOBAL_VCPKG_PATH / ("vcpkg.exe" if os.name == 'nt' else "vcpkg")

    print(f"\n{STATUS_INFO} Linking '{lib_name}' to your project...")
    throbber = Throbber("Extracting CMake hooks...")
    throbber.start()

    try:
        # Enforce two-step workflow using strict regex to avoid substring false positives
        list_check = subprocess.run([str(vcpkg_exe), "list", lib_name], capture_output=True, text=True)
        if not _vcpkg_installed_pattern(lib_name).search(list_check.stdout):
            throbber.stop()
            # Explicit return after fatal() so that if fatal() is ever refactored
            # to raise instead of exit, execution cannot fall through to the extractor
            fatal(f"'{lib_name}' is not installed globally yet. Run 'pain install {lib_name}' first.")
            return

        # Add to vcpkg.json safely
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        added_to_manifest = False
        if lib_name not in manifest.get("dependencies", []):
            manifest.setdefault("dependencies", []).append(lib_name)
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding='utf-8')
            added_to_manifest = True

        # Retrieve the CMake usage instructions from vcpkg
        # Running install on an already-installed package completes instantly and
        # prints the usage block we need to parse
        result = subprocess.run([str(vcpkg_exe), "install", lib_name], capture_output=True, text=True)
        throbber.stop()

        if result.returncode != 0:
            fatal(f"vcpkg install failed while retrieving hooks:\n{result.stderr}")
            return

    except Exception as e:
        throbber.stop()
        fatal(f"An error occurred while linking {lib_name}:\n{e}")
        return

    # Scoped regex extractor delegates to a helper that only captures
    # lines from within the "provides CMake targets:" usage block, preventing false
    # positives from dependency resolution messages elsewhere in the output
    usage_lines = _extract_cmake_usage_lines(result.stdout, lib_name)

    # Inject into the .pain_deps.cmake sidecar
    sidecar_content = sidecar_path.read_text(encoding='utf-8') if sidecar_path.exists() else ""
    hooks_already_present = usage_lines and usage_lines[0] in sidecar_content

    if usage_lines and not hooks_already_present:
        new_code = f"\n# Added by PAIN: {lib_name}\n" + "\n".join(usage_lines) + "\n"
        with sidecar_path.open("a", encoding='utf-8') as f:
            f.write(new_code)

    # Always print a clear summary of what was done, even for header-only
    # libraries that produce no CMake hooks, so the command never looks like a no-op
    manifest_msg = f"added to vcpkg.json" if added_to_manifest else "already in vcpkg.json"

    if not usage_lines:
        print(f"  {STATUS_OK} '{lib_name}' linked ({manifest_msg}).")
        print(f"  {STATUS_INFO} No CMake hooks needed — this appears to be a header-only library.")
    elif hooks_already_present:
        print(f"  {STATUS_OK} '{lib_name}' linked ({manifest_msg}).")
        print(f"  {STATUS_INFO} CMake hooks already present in .pain_deps.cmake.")
    else:
        print(f"  {STATUS_OK} '{lib_name}' linked ({manifest_msg}).")
        print(f"  {STATUS_OK} CMake hooks written to .pain_deps.cmake.")


# UI

def print_logo() -> None:

    if os.name == 'nt':
        os.system('')  # Enable VT100 support on Windows

    logo = r"""
 /$$$$$$$   /$$$$$$  /$$$$$$ /$$   /$$
| $$__  $$ /$$__  $$|_  $$_/| $$$ | $$
| $$  \ $$| $$  \ $$  | $$  | $$$$| $$
| $$$$$$$/| $$$$$$$$  | $$  | $$ $$ $$
| $$____/ | $$__  $$  | $$  | $$  $$$$
| $$      | $$  | $$  | $$  | $$\  $$$
| $$      | $$  | $$ /$$$$$$| $$ \  $$
|__/      |__/  |__/|______/|__/  \__/
"""

    subtitle = "Because setting up C++ projects shouldn't hurt this much!"

    print(f"{C_RED}{logo}{C_RESET}")
    print(f"{C_TERRACOTTA}{subtitle}{C_RESET}\n")


def print_help() -> None:

    print_logo()

    print(f"{C_TERRACOTTA}USAGE:{C_RESET} pain <command> [arguments]\n")

    print(f"{C_RED}PROJECT SETUP{C_RESET}")
    print(f"  {C_YELLOW}init{C_RESET} <name>     Scaffold a new C++ project")
    print(f"  {C_YELLOW}adopt{C_RESET}           Make an existing CMake project PAIN-compatible\n")

    print(f"{C_RED}DEPENDENCIES{C_RESET}")
    print(f"  {C_YELLOW}install{C_RESET} <lib>   Download and compile a library globally")
    print(f"  {C_YELLOW}add{C_RESET} <lib>       Link an installed library to your project")
    print(f"  {C_YELLOW}remove{C_RESET} <lib>    Remove a library")
    print(f"  {C_YELLOW}search{C_RESET} <lib>    Search available packages")
    print(f"  {C_YELLOW}list{C_RESET}            List installed dependencies")
    print(f"  {C_YELLOW}sync{C_RESET}            Regenerate dependency links\n")

    print(f"{C_RED}BUILD & RUN{C_RESET}")
    print(f"  {C_YELLOW}build{C_RESET} [conf]    Build the project (default: Debug)")
    print(f"  {C_YELLOW}run{C_RESET} [-- args]   Run the compiled executable")
    print(f"  {C_YELLOW}clean{C_RESET}           Clean build directory\n")

    print(f"{C_RED}SYSTEM{C_RESET}")
    print(f"  {C_YELLOW}doctor{C_RESET}          Run diagnostics and configure environment\n")


def dashboard() -> None:
    # Show welcome dashboard when no command is provided
    print_logo()
    print(f"  Type {C_YELLOW}pain help{C_RESET} to see all available commands.\n")
    print(f"  {C_TERRACOTTA}Quick Start:{C_RESET} Run {C_YELLOW}pain init <project_name>{C_RESET} to get started.\n")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        dashboard()
    else:

        cmd = sys.argv[1].lower()

        if cmd in ["help", "-help", "--help", "-h"]:
            print_help()

        elif cmd == "init":
            if len(sys.argv) < 3:
                fatal("Please provide a project name. Example: pain init MyApp")
            run_init(sys.argv[2])

        elif cmd == "adopt":
            run_adopt()

        elif cmd == "doctor":
            run_doctor()

        elif cmd == "search":
            if len(sys.argv) < 3:
                fatal("Please provide a library to search for. Example: pain search fmt")
            run_search(sys.argv[2])

        elif cmd == "install":
            if len(sys.argv) < 3:
                fatal("Please provide a library to install. Example: pain install fmt")
            run_install(sys.argv[2])

        elif cmd == "add":
            if len(sys.argv) < 3:
                fatal("Please provide a library to add. Example: pain add fmt")
            run_add(sys.argv[2])

        elif cmd in ["remove", "list", "sync", "build", "run", "clean"]:
            print(f"\n{STATUS_INFO} Command '{cmd}' is not available in this version.\n")

        else:
            print(f"\n{C_RED}Unknown command: '{cmd}'{C_RESET}")
            print(f"Type {C_YELLOW}pain help{C_RESET} for available commands.\n")