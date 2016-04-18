from util import _exec_and_output

def get_active_window():
    active = int(_exec_and_output("xdotool getactivewindow").split()[0])
    if active not in WinList[Desktop]:
        active = None
    return active
