import os

def dashboard():

    if os.name == 'nt':
        # On Windows, this enables ANSI color codes in the terminal; it's a no-op elsewhere.
        import subprocess
        subprocess.run('', shell=True)
        
    # ANSI color codes
    C_RED = "\033[91m"
    C_TERRACOTTA = "\033[38;5;173m"
    C_RESET = "\033[0m"
    
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


if __name__ == "__main__":
    dashboard()