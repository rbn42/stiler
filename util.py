import subprocess
import os
def _exec_and_output(cmd):
    ENCODING = 'utf8'
    return subprocess.check_output(cmd, shell=True).decode(ENCODING)


def _exec(cmd):
    # print(cmd)
    os.system(cmd)
