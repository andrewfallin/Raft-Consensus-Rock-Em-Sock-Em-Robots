import subprocess

# Opens SEVEN separate terminals, one for each process
for process in range(7):
    subprocess.Popen("python start.py", creationflags=subprocess.CREATE_NEW_CONSOLE)

"""
for process in range(5):
    subprocess.Popen("python start.py", creationflags=subprocess.CREATE_NEW_CONSOLE)
"""
