import os
import sys
import subprocess

#CONSTANTS
# ANSI color codes
C_RED = "\033[91m"
C_TERRACOTTA = "\033[38;5;173m"
C_YELLOW = "\033[93m"
C_RESET = "\033[0m"


def print_logo():

    if os.name == 'nt':
        # On Windows, this enables ANSI color codes in the terminal; it's a no-op elsewhere.
        subprocess.run('', shell=True)
    
    # The raw string logo
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


def print_help():
    """The full command list when typing 'pain help'."""
    print_logo()
    print(f"{C_TERRACOTTA}USAGE:{C_RESET} pain <command> [arguments]\n")
    
    print(f"{C_RED}PROJECT SETUP{C_RESET}")
    print(f"  {C_YELLOW}init{C_RESET} <name>    Scaffold a brand new C++ project")
    print(f"  {C_YELLOW}adopt{C_RESET}          Inject PAIN hooks into an existing CMake project\n")
    
    print(f"{C_RED}DEPENDENCIES{C_RESET}")
    print(f"  {C_YELLOW}add{C_RESET} <lib>      Download and auto-link a library")
    print(f"  {C_YELLOW}remove{C_RESET} <lib>   Remove a library and clean up links")
    print(f"  {C_YELLOW}search{C_RESET} <lib>   Search the local vcpkg registry")
    print(f"  {C_YELLOW}list{C_RESET}           Show all currently installed dependencies")
    print(f"  {C_YELLOW}sync{C_RESET}           Regenerate the CMake link file from vcpkg.json\n")
    
    print(f"{C_RED}BUILD & RUN{C_RESET}")
    print(f"  {C_YELLOW}build{C_RESET} [conf]   Compile the project (default: Debug)")
    print(f"  {C_YELLOW}run{C_RESET} [-- args]  Find and execute the compiled binary")
    print(f"  {C_YELLOW}clean{C_RESET}          Safely delete the build/ folder\n")
    
    print(f"{C_RED}SYSTEM{C_RESET}")
    print(f"  {C_YELLOW}doctor{C_RESET}         Check compiler status and configure global caches\n")


def dashboard():

    print_logo()
    print(f"  Type {C_YELLOW}pain help{C_RESET} to see all commands.\n")
    print(f"  {C_TERRACOTTA}Quick Start:{C_RESET} Run {C_YELLOW}pain init <project_name>{C_RESET} to begin.\n")


if __name__ == "__main__":

    if len(sys.argv) < 2:
        dashboard()
    else:
        # Route the commands
        cmd = sys.argv[1].lower()
        
        if cmd in ["help", "-help", "--help", "-h"]:
            print_help()

        elif cmd == "init":
            pass

        else:
            print(f"{C_RED}Unknown command: '{cmd}'{C_RESET}\n")
            print(f"Type {C_YELLOW}pain help{C_RESET} for a list of valid commands.\n")