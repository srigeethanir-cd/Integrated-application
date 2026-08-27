import subprocess


class CommandRunner:
    def execute(self, command: str):
        return subprocess.run(command, shell=True, check=False)
