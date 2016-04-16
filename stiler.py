#!/usr/bin/python
# -*- coding: UTF-8 -*-

############################################################################
# Copyright (c) 2009   unohu <unohu0@gmail.com>                            #
#                                                                          #
# Permission to use, copy, modify, and/or distribute this software for any #
# purpose with or without fee is hereby granted, provided that the above   #
# copyright notice and this permission notice appear in all copies.        #
#                                                                          #
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES #
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF         #
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR  #
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES   #
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN    #
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF  #
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.           #
#                                                                          #
############################################################################

"""
Tiling window on any window manager. 

Usage:
  stiler.py layout (next|prev)
  stiler.py (focus|swap) (up|down|left|right)
  stiler.py (grow|shrink) (height|width)
  stiler.py cycle 
  stiler.py anticycle 
  stiler.py -h | --help

Options:
  -h --help     Show this screen.
"""

import os
import re
import subprocess
import time


def _exec_and_output(cmd):
    ENCODING = 'utf8'
    return subprocess.check_output(cmd, shell=True).decode(ENCODING)


def _exec(cmd):
    # print(cmd)
    os.system(cmd)

BottomPadding = 20
TopPadding = 20
LeftPadding = 20
RightPadding = 20
WinTitle = 28
WinBorder = 5
NavigateAcrossWorkspaces = True  # TODO availabe in Unity7
TempFile = "/dev/shm/.stiler_db"

r_wmctrl_lG = '^([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+(.+)$'
r_wmctrl_d = '(\d)+.+?(\d+)x(\d+).+?(\d+),(\d+).+?(\d+),(\d+).+?(\d+)x(\d+)'


def initialize():
    desk_output = _exec_and_output("wmctrl -d").strip().split("\n")
    desk_list = [line.split()[0] for line in desk_output]

    current = [x for x in desk_output if x.split()[1] == "*"][0]
    current = re.findall(r_wmctrl_d, current.strip())[0]
    desktop = current[0]
    orig_x, orig_y, width, height = current[-4:]

    s = _exec_and_output(
        "xdpyinfo | grep 'dimension' | awk -F: '{ print $2 }' | awk '{ print $1 }' ")
    x, y = s.split('x')
    resx, resy = int(x), int(y)

    win_output = _exec_and_output("wmctrl -lG").strip().split("\n")

    win_filtered = []
    win_filtered_all = []
    for win in win_output:
        _, _, x, y, w, h, host, name = re.findall(r_wmctrl_lG, win)[0]
        x, y = int(x), int(y)
        if host == 'N/A':
            continue
        if name in ['<unknown>', 'x-nautilus-desktop',
                    'unity-launcher', 'unity-panel'] + ['Hud',
                                                        'unity-dash', 'Desktop',
                                                        'screenkey',
                                                        'XdndCollectionWindowImp']:
            continue
        win_filtered_all.append(win)
        if x < 0 or x >= resx or y < 0 or y >= resy:
            continue
        win_filtered.append(win)
        # TODO use xwininfo to exclude minimized windows

    win_list = {}
    win_list_all = {}
    for desk in desk_list:
        win_list[desk] = [int(x.split()[0], 16)
                          for x in win_filtered if x.split()[1] == desk]
        win_list_all[desk] = [int(x.split()[0], 16)
                              for x in win_filtered_all if x.split()[1] == desk]

    return desktop, orig_x, orig_y, width, height, win_list, win_list_all, win_filtered, win_filtered_all


def get_active_window():
    active = int(_exec_and_output("xdotool getactivewindow").split()[0])
    if active not in WinList[Desktop]:
        active = None
    return active


def store(object, file=TempFile):
    with open(file, 'w') as f:
        f.write(str(object))


def retrieve(file=TempFile):
    if os.path.exists(file):
        return eval(open(file).read())
    else:
        return {}


(Desktop, OrigXstr, OrigYstr, MaxWidthStr,
 MaxHeightStr, WinList, WinListAll, WinPosInfo, WinPosInfoAll) = initialize()
MaxWidth = int(MaxWidthStr) - LeftPadding - RightPadding
MaxHeight = int(MaxHeightStr) - TopPadding - BottomPadding
OrigX = int(OrigXstr) + LeftPadding
OrigY = int(OrigYstr) + TopPadding
data_temp = retrieve()
OldWinList = data_temp.get('winlist', {})

WinPosInfo = [re.findall(r_wmctrl_lG, w)[0] for w in WinPosInfo]
WinPosInfo = {int(_id, 16): (_name, [int(x), int(y), int(
    w), int(h)]) for _id, _ws, x, y, w, h, _host, _name in WinPosInfo}
for _id in WinPosInfo:
    WinPosInfo[_id][1][1] += -72 + 44

WinPosInfoAll = [re.findall(r_wmctrl_lG, w)[0] for w in WinPosInfoAll]
WinPosInfoAll = {int(_id, 16): (_name, [int(x), int(y), int(
    w), int(h)]) for _id, _ws, x, y, w, h, _host, _name in WinPosInfoAll}
for _id in WinPosInfoAll:
    WinPosInfoAll[_id][1][1] += -72 + 44

WinPosInfo = WinPosInfoAll


def get_simple_tile(wincount):
    MwFactor = 0.55
    rows = wincount - 1
    layout = []
    if rows == 0:
        layout.append(
            (OrigX, OrigY, MaxWidth, MaxHeight - WinTitle - WinBorder))
        return layout
    else:
        layout.append((OrigX, OrigY, int(MaxWidth * MwFactor),
                       MaxHeight - WinTitle - WinBorder))

    x = OrigX + int((MaxWidth * MwFactor) + (2 * WinBorder))
    width = int((MaxWidth * (1 - MwFactor)) - 2 * WinBorder)
    height = int(MaxHeight / rows - WinTitle - WinBorder)

    for n in range(0, rows):
        y = OrigY + int((MaxHeight / rows) * (n))
        layout.append((x, y, width, height))

    return layout


def change_tile(reverse=False):
    # TODO available tiling layouts
    tiles_map = {
        'col2_l': lambda w: get_columns_tile2(w, reverse=False, cols=2),
        'col2_r': lambda w: get_columns_tile2(w, reverse=True, cols=2),
        'simple': get_simple_tile,
        'col1': lambda w: get_columns_tile2(w, reverse=False, cols=1),
        'horiz': get_horiz_tile,
        'vertical': get_vertical_tile,
        'fair': get_fair_tile,
        'autogrid': get_autogrid_tile,
        'maximize': maximize,
        'minimize': minimize,
    }

    winlist = create_win_list(WinList)
    if len(winlist) < 1:
        return

    if len(winlist) < 2:
        TILES = []
    elif len(winlist) % 2 == 0:
        TILES = ['col2_l']
    else:
        TILES = ['col2_l', 'col2_r']
    if len(winlist) > 3:
        TILES.append('simple')
    if len(winlist) > 1:
        TILES.append('col1')
    TILES.append('maximize')

    # TODO unable to compare windows's numbers between different workspaces
    if not len(winlist) == len(OldWinList[Desktop]):
        shift = 0
    elif reverse:
        shift = - 1
    else:
        shift = 1

    t = data_temp.get('tile', None)
    if 0 == shift and t in tiles_map:
        pass
    elif t in TILES:
        i0 = TILES.index(t)
        i1 = i0 + shift
        t = TILES[i1 % len(TILES)]
    else:
        t = TILES[0]

    tile = tiles_map[t](len(winlist))
    if not None == tile:
        arrange(tile, winlist)
    save_window_layout(tile, winlist, tile=t)


def get_vertical_tile(wincount):
    layout = []
    y = OrigY
    width = int(MaxWidth / wincount)
    height = MaxHeight - WinTitle - WinBorder
    for n in range(0, wincount):
        x = OrigX + n * width
        layout.append((x, y, width, height))

    return layout


def get_horiz_tile(wincount):
    layout = []
    x = OrigX
    height = int(MaxHeight / wincount - WinTitle - WinBorder)
    width = MaxWidth
    for n in range(0, wincount):
        y = OrigY + int((MaxHeight / wincount) * (n))
        layout.append((x, y, width, height))

    return layout

# from https://bbs.archlinux.org/viewtopic.php?id=64100&p=6  #150
import math


def get_autogrid_tile(wincount):
    layout = []
    rows = int(math.floor(math.sqrt(wincount)))
    rowheight = int(MaxHeight / rows)
    windowsleft = wincount
    for row in range(rows):
        cols = min(int(math.ceil(float(wincount) / rows)), windowsleft)
        windowsleft -= cols
        colwidth = MaxWidth / cols
        for col in range(cols):
            layout.append((OrigX + colwidth * col, OrigY + row *
                           rowheight, colwidth, rowheight - WinTitle - WinBorder))
    return layout[:wincount]
# end https://bbs.archlinux.org/viewtopic.php?id=64100&p=6  #150


def get_columns_tile2(wincount, reverse=False, cols=2):
    if wincount < 2:
        return get_vertical_tile(wincount)
    layout = []
    colwidth = int(MaxWidth / cols)
    windowsleft = wincount
    if reverse:
        _range = range(cols - 1, -1, -1)
    else:
        _range = range(cols)
    for col in _range:
        rows = min(int(math.ceil(float(wincount) / cols)), windowsleft)
        windowsleft -= rows
        rowheight = MaxHeight / rows
        for row in range(rows):
            layout.append((OrigX + colwidth * col + WinBorder, OrigY + row *
                           rowheight, colwidth - 2 * WinBorder, rowheight - WinTitle - WinBorder))
    return layout[:wincount]
# from https://bbs.archlinux.org/viewtopic.php?id=64100&p=7 #151


def get_columns_tile(wincount, ncolumns):
    # 2nd term rounds up if num columns not a factor of
    # num windows; this leaves gaps at the bottom
    nrows = (wincount / ncolumns) + int(bool(wincount % ncolumns))

    layout = []
    x = OrigX
    y = OrigY

    height = int(MaxHeight / nrows - WinTitle - WinBorder)
    width = int(MaxWidth / ncolumns - 2 * WinBorder)

    for n in range(0, wincount):
        column = n % ncolumns
        row = n / ncolumns

        x = OrigX + column * width
        y = OrigY + (int((MaxHeight / nrows) * (row)))
        layout.append((x, y, width, height))

    return layout


def get_fair_tile(wincount):
    import math
    ncolumns = int(math.ceil(math.sqrt(wincount)))
    return get_columns_tile(wincount, ncolumns)
# end https://bbs.archlinux.org/viewtopic.php?id=64100&p=7 #151


def unmaximize_one(windowid):
    command = " wmctrl -i -r %d -bremove,maximized_vert,maximized_horz" % windowid
    _exec(command)


def maximize_one(windowid):
    command = " wmctrl -i -r %d -badd,maximized_vert,maximized_horz" % windowid
    _exec(command)


def minimize_one(windowid):
    command = 'xdotool windowminimize %d' % windowid
    _exec(command)


# def move_window(windowid, PosX, PosY, Width, Height):
def move_window(windowid, x, y, w, h):
    # Unmaximize window
    unmaximize_one(windowid)
    # Now move it
    _name = WinPosInfo[windowid][0]
    if 'tilda' == _name:
        h += WinTitle
    command = "wmctrl -i -r %d -e 0,%d,%d,%d,%d" % (windowid, x, y, w, h)
    _exec(command)
    #command = "wmctrl -i -r " + windowid + " -b remove,hidden,shaded"
#    _exec(command)
#    command = 'xdotool windowmap "%s"' % windowid
#    command = 'xdotool windowactivate "%s"' % windowid


def raise_window(windowid):
    if False:
        command = 'xdotool windowactivate %d' % windowid
    command = "wmctrl -i -a %d" % windowid
    _exec(command)


def compare_win_list(newlist, oldlist):
    templist = []
    for window in oldlist:
        if newlist.count(window) != 0:
            templist.append(window)
    for window in newlist:
        if oldlist.count(window) == 0:
            templist.append(window)
    return templist


def create_win_list(winlist):
    Windows = winlist[Desktop]

    if OldWinList == {}:
        pass
    else:
        OldWindows = OldWinList[Desktop]
        if Windows == OldWindows:
            pass
        else:
            Windows = compare_win_list(Windows, OldWindows)

    return Windows


def arrange(layout, windows):
    for win, lay in zip(windows, layout):
        move_window(win, *lay)


def save_window_layout(layout, windows, tile=None):
    if not tile == None:
        data_temp['tile'] = tile
    WinList[Desktop] = windows
    data_temp['winlist'] = WinList
    store(data_temp)


def get_current_tile(wins, posinfo):
    l = []
    for _id in wins:
        _name, _pos = posinfo[_id]
        x, y, w, h = _pos
        if 'tilda' in _name:
            h -= WinTitle
            y += WinTitle
        l.append([x, y, w, h])
    return l


def cycle(reverse=False):
    winlist = create_win_list(WinList)
    lay = get_current_tile(winlist, WinPosInfo)
    shift = -1 if reverse else 1
    winlist = winlist[shift:] + winlist[:shift]
    arrange(lay, winlist)
    save_window_layout(lay, winlist)

    active = get_active_window()
    i0 = winlist.index(active)
    i1 = (i0 + shift) % len(winlist)
    raise_window(winlist[i1])


def getkdtree(winlist, lay):
    from kdtree import kdtree
    tolerance = 0.0
    t = tolerance
    dy = 10
    sw, sh = 1920 * 10, 1080 * 10
    origin_lay = [[x, y, x + w, y + h] for x, y, w, h in lay]
    normalized = [[(x + t) / sw, (y + dy + t) / sh, (x + w - t) /
                   sw, (y + dy + h - t) / sh] for x, y, w, h in lay]
    _tree, _map = kdtree(zip(normalized, winlist, origin_lay))
    return _tree, _map


def resize(resize_width, resize_height):
    '''
    Adjust non-overlapping layout.
    '''
    winlist = create_win_list(WinList)
    lay = get_current_tile(winlist, WinPosInfo)
    active = get_active_window()
    if None==active:
        return
    _tree, _map = getkdtree(winlist, lay)
    current_node=_map[active]

    if len(current_node.path) % 2 == 0:
        resize_current=resize_height
        resize_parent=resize_width
        index_current=3
        index_parent=2
    else:
        resize_current=resize_width
        resize_parent=resize_height
        index_current=2
        index_parent=3

    regularize_node=None

    if not resize_current==0:
        if not current_node.overlap  :
            if not None==current_node.parent:
                current_node.modified = True
                current_node.position[index_current] += resize_current
                regularize_node=current_node.parent
    if not resize_parent==0:
        if not None==current_node.parent :
            if not current_node.parent.overlap:
                if not None== current_node.parent.parent:
                    current_node.parent.modified = True
                    current_node.parent.position[index_parent] += resize_parent
                    regularize_node=current_node.parent.parent


    # regularize k-d tree
    from kdtree import regularize
    regularize(regularize_node,border=(2*WinBorder,WinBorder+WinTitle))
    # reload k-d tree
    from kdtree import getLayoutAndKey
    a, b = (getLayoutAndKey(_tree))
    arrange(a, b)

def swap_kdtree(target):
    '''
    Adjust non-overlapping layout.
    '''

    active = get_active_window()
    if None==active:
        return True

    winlist = create_win_list(WinList)
    lay = get_current_tile(winlist, WinPosInfo)
    _tree, _map = getkdtree(winlist, lay)
    current_node=_map[active]

    if len(current_node.path) % 2 == 0:
        promote = target in ['right','left']
    else:   
        promote = target in ['down','up']
    if promote:
        shift=0 if target in ['left','up'] else 1
        current_node.parent.children.remove(current_node)   
        regularize_node=current_node.parent.parent
        index_parent=regularize_node.children.index(current_node.parent)
        regularize_node.children.insert(index_parent+shift,current_node)
    else:
        shift=-1 if target in ['left','up'] else 0
        regularize_node=current_node.parent
        index_current=regularize_node.children.index(current_node)
        regularize_node.children.remove(current_node)
        new_parent=regularize_node.children[index_current+shift]
        if new_parent.leaf:
            from kdtree import create_parent
            new_parent=create_parent(new_parent)
        new_parent.children.append(current_node)


    # regularize k-d tree
    from kdtree import regularize
    regularize(regularize_node,border=(2*WinBorder,WinBorder+WinTitle))
    # reload k-d tree
    from kdtree import getLayoutAndKey
    a, b = (getLayoutAndKey(regularize_node))
    arrange(a, b)
    return True

def swap(target):
    winlist = create_win_list(WinList)
    lay = get_current_tile(winlist, WinPosInfo)

    active = get_active_window()
    if None == active:
        return

    target = find(active, target, winlist, WinPosInfo)
    if None == target:
        return

    i0 = winlist.index(active)
    i1 = winlist.index(target)

    arrange([lay[i0], lay[i1]], [winlist[i1], winlist[i0]])

    winlist[i0], winlist[i1] = winlist[i1], winlist[i0]
    save_window_layout(lay, winlist)


def find(center, target, winlist, posinfo):
    '''
    find the nearest window in the target direction.
    '''
    lay = get_current_tile(winlist, posinfo)
    cal_center = lambda x, y, w, h: [x + w / 2.2, y + h / 2.2]
    if None == center:
        lay_center = MaxWidth / 2.0, MaxHeight / 2.0
    else:
        m = {w: l for w, l in zip(winlist, lay)}
        lay_center = cal_center(* m[center])
    _min = -1
    _r = None
    for w, l in zip(winlist, lay):
        l = cal_center(*l)
        bias1, bias2 = 1.0, 1.0
        bias = 4.0
        if target == 'down':
            delta = l[1] - lay_center[1]
            delta2 = (l[1] - lay_center[1])**2 - (l[0] - lay_center[0])**2
            bias1 = bias
        if target == 'up':
            delta = lay_center[1] - l[1]
            delta2 = (l[1] - lay_center[1])**2 - (l[0] - lay_center[0])**2
            bias1 = bias
        if target == 'right':
            delta = l[0] - lay_center[0]
            delta2 = (l[0] - lay_center[0])**2 - (l[1] - lay_center[1])**2
            bias2 = bias
        if target == 'left':
            delta = lay_center[0] - l[0]
            delta2 = (l[0] - lay_center[0])**2 - (l[1] - lay_center[1])**2
            bias2 = bias
        distance = bias1 * (l[0] - lay_center[0])**2 + \
            bias2 * (l[1] - lay_center[1])**2
        if delta > 0 and delta2 > 0:
            if _min == -1 or distance < _min:
                _min = distance
                _r = w
    return _r


def focus(target):
    if NavigateAcrossWorkspaces:
        Windows = create_win_list(WinListAll)
    else:
        Windows = create_win_list(WinList)

    active = get_active_window()

    if NavigateAcrossWorkspaces:
        target = find(active, target, Windows, WinPosInfoAll)
    else:
        target = find(active, target, Windows, WinPosInfo)
    if None == target:
        return
    i1 = Windows.index(target)
    raise_window(Windows[i1])


def minimize(wincount):
    winlist = create_win_list(WinList)
    for win in winlist:
        minimize_one(win)


def maximize(wincount):
    active = get_active_window()
    winlist = create_win_list(WinList)
    for win in winlist:
        maximize_one(win)
    raise_window(active)
    return None

    maximize_one(active)
    return None

if __name__ == '__main__':
    from docopt import docopt
    arguments = docopt(__doc__)

    for target in ('up', 'down', 'left', 'right'):
        if arguments[target]:
            break

    if False:
        pass
    elif arguments['cycle']:
        cycle()
    elif arguments['anticycle']:
        cycle(reverse=True)
    elif arguments['swap']:
        #if swap_kdtree(target):
        swap(target)
    elif arguments['focus']:
        focus(target)
    elif arguments['layout']:
        assert not arguments['next'] == arguments['prev']
        change_tile(reverse=arguments['prev'])
    elif arguments['grow']:
        if arguments['width']:
            resize(20, 0)
        else:
            resize(0, 20)
    elif arguments['shrink']:
        if arguments['width']:
            resize(-20, 0)
        else:
            resize(0, -20)
