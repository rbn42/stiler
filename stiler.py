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
  stiler.py (focus|move|swap) (up|down|left|right)
  stiler.py (grow|shrink) (height|width)
  stiler.py cycle 
  stiler.py anticycle 
  stiler.py (save|load) <layout_id>
  stiler.py -h | --help

Options:
  -h --help     Show this screen.
"""

import os
import re
import subprocess
import time
from config import *
import config
import xutils


from util import _exec_and_output
from util import _exec
def get_active_window():
    active = int(_exec_and_output("xdotool getactivewindow").split()[0])
    if active not in WinList[Desktop]:
        active = None
    return active
#from util import _exec_and_output
from xutils import get_active_window
#from xdotool import get_active_window



r_wmctrl_lG = '^([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+(.+)$'
r_wmctrl_d = '(\d)+.+?(\d+)x(\d+).+?(\d+),(\d+).+?(\d+),(\d+).+?(\d+)x(\d+)'


def initialize1():
    desk_output = _exec_and_output("wmctrl -d").strip().split("\n")

    current = [x for x in desk_output if x.split()[1] == "*"][0]
    current = re.findall(r_wmctrl_d, current.strip())[0]
    desktop, _, _, desktop_x, desktop_y, orig_x, orig_y, width, height = current

    return desktop, desktop_x, desktop_y, orig_x, orig_y, width, height


def initialize2(desktop):
    cmd = "xdpyinfo | grep 'dimension' | awk -F: '{ print $2 }' | awk '{ print $1 }' "
    s = _exec_and_output(cmd)
    x, y = s.split('x')
    resx, resy = int(x), int(y)

    win_output = _exec_and_output("wmctrl -lG").strip().split("\n")

    win_list = []
    win_list_all = []
    WinPosInfoAll = {}
    for win in win_output:

        winid, _desktop, x, y, w, h, host, name = re.findall(r_wmctrl_lG, win)[
            0]

        if not _desktop == desktop:
            continue
        if host == 'N/A':
            continue
        if name in config.EXCLUDE_APPLICATIONS:
            continue

        winid, x, y, w, h = int(winid, 16), int(x), int(y), int(w), int(h)

        win_list_all.append(winid)
        WinPosInfoAll[winid] = name, [x, y - 72 + 44, w, h]

        if x < 0 or x >= resx or y < 0 or y >= resy:
            continue

        win_list.append(winid)
        # TODO use xwininfo to exclude minimized windows

    return win_list, win_list_all,  WinPosInfoAll




def get_last_active_window():
    for active in PERSISTENT_DATA.get('active_history', []):
        if active in WinList:
            if not active==get_active_window():
                return active
    return None



def get_simple_tile(wincount):
    MwFactor = 0.55
    rows = wincount - 1
    layout = []
    if rows == 0:
        layout.append(layout_shift(0, 0, MaxWidth, MaxHeight))
        return layout
    else:
        layout.append(layout_shift(0, 0, int(MaxWidth * MwFactor),
                                   MaxHeight))

    x = int((MaxWidth * MwFactor))
    width = int((MaxWidth * (1 - MwFactor)))
    height = int(MaxHeight / rows)

    for n in range(0, rows):
        y = int((MaxHeight / rows) * (n))
        layout.append(layout_shift(x, y, width, height))

    return layout


def change_tile_or_insert_new_window(shift):
    if len(WinList) < 1:
        return

    if len(WinList) ==1+ len(OldWinList): 
        if insert_focused_window_into_kdtree():
            return
    if len(WinList) == len(OldWinList):
        change_tile(shift)
    else:
        change_tile(0)




def insert_focused_window_into_kdtree():
    active=get_active_window()
    if None==active:
        return False
    last_active=get_last_active_window()
    if None==last_active:
        return False
    if insert_window_into_kdtree(active,last_active):
        PERSISTENT_DATA['winlist'] = WinList
        return True
    return False


def regularize_kd_tree(regularize_node,
        min_width=config.MIN_WINDOW_WIDTH,
        min_height=config.MIN_WINDOW_HEIGHT):
    if None == regularize_node:
        return False
    # regularize k-d tree
    from kdtree import regularize
    regularize(regularize_node, border=(2 * WinBorder, WinBorder + WinTitle))

    # load k-d tree
    from kdtree import getLayoutAndKey
    a, b, reach_size_limit = getLayoutAndKey(
        regularize_node, min_width=min_width, min_height=min_height)
    if reach_size_limit:
        return False
    arrange(a, b)
    return True


def detect_overlap():
    t = PERSISTENT_DATA.get('tile', None)
    OVERLAP_LAYOUT = ['minimize', 'maximize']
    if not None == t and t not in OVERLAP_LAYOUT:
        current_layout = get_current_tile(WinList, WinPosInfo)
        return getkdtree(WinList, current_layout)[0].overlap


def change_tile(shift):
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

    #for rotated screen
    if MaxWidth < MaxHeight:
        if len(winlist) > 1:
            TILES=['col1']
        TILES.append('maximize')

    # TODO unable to compare windows's numbers between different workspaces

    t = PERSISTENT_DATA.get('tile', None)

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

    PERSISTENT_DATA['overall_position'] = None
    PERSISTENT_DATA['tile'] = t
    PERSISTENT_DATA['winlist'] = winlist


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
            layout.append(layout_shift(colwidth * col, row *
                                       rowheight, colwidth, rowheight))
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
            layout.append(layout_shift(
                colwidth * col,
                row * rowheight,
                colwidth,
                rowheight))
    return layout[:wincount]


def layout_shift(x, y, w, h):
    return OrigX + x + WinBorder, OrigY + y + WinBorder, w - 2 * WinBorder, h - WinTitle - 2 * WinBorder
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
    if check_notitle1(_name):
        h += WinTitle
    if check_notitle2(_name):
        y += WinTitle
    w=xutils.moveandresize(windowid,x,y,w,h)
    return w
def move_wmctrl(windowid,x,y,w,h):
    command = "wmctrl -i -r %d -e 0,%d,%d,%d,%d" % (windowid, x, y, w, h)
    _exec(command)
    #command='xdotool windowmove  %d %d %d' %(windowid,x,y)
    # print(command)
    #command='xdotool windowsize  %d %d %d' %(windowid,w,h)
    # print(command)
    #_exec(command)
    #command = "wmctrl -i -r " + windowid + " -b remove,hidden,shaded"
#    _exec(command)
#    command = 'xdotool windowmap "%s"' % windowid
#    command = 'xdotool windowactivate "%s"' % windowid


def raise_window(windowid):
    if False:
        command = 'xdotool windowactivate %d' % windowid
    command = "wmctrl -i -a %d" % windowid
    _exec(command)


def create_win_list(winlist):
    new = winlist
    old = OldWinList
    Windows = [w for w in old if w in new] + [w for w in new if w not in old]
    return Windows


def arrange(layout, windows):
    l=[]
    for win, lay in zip(windows, layout):
        w=move_window(win, *lay)
        l.append(w)
    for w in l:
        w.get_geometry()
            


def get_current_tile(wins, posinfo):
    l = []
    for _id in wins:
        _name, _pos = posinfo[_id]
        x, y, w, h = _pos
        if check_notitle1(_name):
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

    active = get_active_window()
    i0 = winlist.index(active)
    i1 = (i0 + shift) % len(winlist)
    raise_window(winlist[i1])

    PERSISTENT_DATA['winlist'] = winlist


def check_notitle1(name):
    for n in config.NOTITLE1:
        if n in name:
            return True
    return False


def check_notitle2(name):
    for n in config.NOTITLE2:
        if n in name:
            return True
    return False


def getkdtree(winlist, lay):
    # begin "normalize positions"
    '''
    The kdtree function only accept values between 0 and 1.
    '''
    tolerance = 0.0
    t = tolerance
    dy = 10
    sw, sh = 2000 * 10, 1000 * 10
    normalized = [[(x + t) / sw, (y + dy + t) / sh, (x + w - t) /
                   sw, (y + dy + h - t) / sh] for x, y, w, h in lay]
    # end "normalize positions"

    # begin "generate k-d tree"
    origin_lay = [[x, y, x + w, y + h] for x, y, w, h in lay]
    from kdtree import kdtree
    _tree, _map = kdtree(zip(normalized, winlist, origin_lay))
    # end "generate k-d tree"

    # begin "reload old root"
    '''
    wmctrl cannot resize some applications precisely, like gnome-terminal. The side effect is that the overall window size decreases.
    Reloading old root node position somehow helps prevent these windows shrink too much over time. When the k-d tree is regularized, the size of the root node will be passed to leaves.
    '''
    p1 = _tree.position
    p2 = PERSISTENT_DATA.get('overall_position', None)
    if not None == p2:
        x0, y0, x1, y1 = p2
        p2 = [max(1, x0), max(1, y0), min(x1, int(MaxWidthStr)),
              min(y1, int(MaxHeightStr))]
    if None == p2:
        PERSISTENT_DATA['overall_position'] = [i for i in p1]
    elif p1[0] < p2[0] or p1[1] < p2[1] or p1[2] > p2[2] or p1[3] > p2[3]:
        PERSISTENT_DATA['overall_position'] = [i for i in p1]
    else:
        # Root nodes
        pass
        #_tree.position = [i for i in p2]
        #_tree.children[0].position = [i for i in p2]
        #_tree.children[0].children[0].position = [i for i in p2]
    # end "reload old root"
    return _tree, _map


def resize(resize_width, resize_height):
    if resize_kdtree(resize_width, resize_height):
        return True
    return moveandresize([0, 0, resize_width, resize_height])


def move(target):
    if move_kdtree(target, allow_create_new_node=True):
        return True
    if move_kdtree(target, allow_create_new_node=False):
        return True
    target = {'left': [-config.MOVE_STEP, 0, 0, 0],
              'down': [0, config.MOVE_STEP, 0, 0],
              'up': [0, -config.MOVE_STEP, 0, 0],
              'right': [config.MOVE_STEP, 0, 0, 0], }[target]
    return moveandresize(target)


def moveandresize(target):
    active = get_active_window()
    # cannot find target window
    if None == active:
        return False
#    lay = get_current_tile([active], WinPosInfo)[0]
    lay=xutils.get_position_and_size(active)
    for i in range(4):
        lay[i]+=target[i] 
    arrange([lay],[active])

    return True


def resize_kdtree(resize_width, resize_height):
    '''
    Adjust non-overlapping layout.
    '''

    winlist = create_win_list(WinList)
    # ignore layouts with less than 2 windows
    if len(winlist) < 2:
        return False

    active = get_active_window()
    # can find target window
    if None == active:
        return False

    lay = get_current_tile(winlist, WinPosInfo)
    # generate k-d tree
    _tree, _map = getkdtree(winlist, lay)
    current_node = _map[active]

    # determine the size of current node and parent node.
    if len(current_node.path) % 2 == 0:
        resize_current = resize_height
        resize_parent = resize_width
        index_current = 3
        index_parent = 2
    else:
        resize_current = resize_width
        resize_parent = resize_height
        index_current = 2
        index_parent = 3

    regularize_node = None

    # resize nodes
    if not resize_current == 0:
        if not current_node.overlap:
            if not None == current_node.parent:
                node = current_node
                index = index_current
                _resize = resize_current
                node.modified = True
                regularize_node = node.parent
                # invert the operation if the node is the last child of its
                # parent
                if regularize_node.children[-1] == node:
                    node.position[index] -= _resize
                else:
                    node.position[index] += _resize

    if not resize_parent == 0:
        if not None == current_node.parent:
            if not current_node.parent.overlap:
                if not None == current_node.parent.parent:
                    node = current_node.parent
                    index = index_parent
                    _resize = resize_parent
                    node.modified = True
                    regularize_node = node.parent
                    # invert the operation if the node is the last child of its
                    # parent
                    if regularize_node.children[-1] == node:
                        node.position[index] -= _resize
                    else:
                        node.position[index] += _resize

    if None == regularize_node:
        return False
    regularize_node = regularize_node.parent

    return regularize_kd_tree(regularize_node)

def insert_window_into_kdtree(winid,target):
    winlist=[w for w in WinList if not w==winid]
    lay = get_current_tile(winlist, WinPosInfo)
    _tree, _map = getkdtree(winlist, lay)
    target_node = _map[target]
    if target_node.parent.overlap:
        return False
    from kdtree import create_sibling
    node=create_sibling(target_node)
    node.key=winid
    node.leaf=True
    return regularize_kd_tree(node.parent)

def move_kdtree(target, allow_create_new_node=True):
    '''
    Adjust non-overlapping layout.
    '''

    active = get_active_window()
    # can find target window
    if None == active:
        return False

    winlist = WinList  # create_win_list(WinList)
    # ignore layouts with less than 2 windows
    if len(winlist) < 2:
        return False

    lay = get_current_tile(winlist, WinPosInfo)
    # generate k-d tree
    _tree, _map = getkdtree(winlist, lay)
    current_node = _map[active]

    # whether promote node to its parent's level
    if len(current_node.path) % 2 == 0:
        promote = target in ['right', 'left']
    else:
        promote = target in ['down', 'up']
    shift = 0 if target in ['left', 'up'] else 1

    if promote:
        current_node.parent.children.remove(current_node)
        regularize_node = current_node.parent.parent
        index_parent = regularize_node.children.index(current_node.parent)
        regularize_node.children.insert(index_parent + shift, current_node)
    else:
        regularize_node = current_node.parent
        index_current = regularize_node.children.index(current_node)
        regularize_node.children.remove(current_node)
        '''
        If there is no more nodes at the target direction, promote the current node.
        '''
        if 0 <= index_current - 1 + shift < len(regularize_node.children):

            # If there are is only one sibling node, promote them both.
            if len(regularize_node.children) == 1:
                #
                shift = -1 if target in ['left', 'up'] else 1
                regularize_node.children.insert(
                    index_current + shift, current_node)
            else:
                new_parent = regularize_node.children[
                    index_current - 1 + shift]
                # If there is a leaf node at the target direction, build a new
                # parent node for the leaf node and the current node.
                _swap = False or not allow_create_new_node
                if new_parent.leaf and not _swap:
                    # But allow no more than one branch for each node
                    for sibling in new_parent.parent.children:
                        if not sibling.leaf:
                            # Just swap them.
                            _swap = True
                            break
                    else:
                        from kdtree import create_parent
                        new_parent = create_parent(new_parent)
                if _swap:
                    shift = -1 if target in ['left', 'up'] else 1
                    regularize_node.children.insert(
                        index_current + shift, current_node)
                else:
                    new_parent.children.append(current_node)
        else:
            # promote the current node.
            regularize_node = current_node.parent.parent.parent
            index_current = regularize_node.children.index(
                current_node.parent.parent)
            regularize_node.children.insert(
                index_current + shift, current_node)

        if len(regularize_node.children) == 1:
            regularize_node = regularize_node.parent

    # remove nodes which has only one child
    from kdtree import remove_single_child_node
    remove_single_child_node(regularize_node)

    if regularize_node.overlap:
        return False

    # regularize k-d tree
    regularize_node = regularize_node.parent
    return regularize_kd_tree(regularize_node,min_width=1,min_height=1)


def swap(target):

    winlist = create_win_list(WinList)
    active = get_active_window()

    if None == active:
        return False

    target_window_id = find_kdtree(active, target, allow_parent_sibling=False)

    if None == target_window_id:
        target_window_id = find(active, target, winlist, WinPosInfo)

    if None == target_window_id:
        target_window_id = find_kdtree(active, target, allow_parent_sibling=True)

    if None == target_window_id:
        return False

    i0 = winlist.index(active)
    i1 = winlist.index(target_window_id)

    lay = get_current_tile(winlist, WinPosInfo)
    arrange([lay[i0], lay[i1]], [winlist[i1], winlist[i0]])

    winlist[i0], winlist[i1] = winlist[i1], winlist[i0]
    PERSISTENT_DATA['winlist'] = winlist
    return True


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

    active = get_active_window()

    target_window_id = find_kdtree(active, target, allow_parent_sibling=False)

    if None == target_window_id:
        if config.NavigateAcrossWorkspaces:
            Windows = WinListAll
        else:
            Windows = WinList
        target_window_id = find(active, target, Windows, WinPosInfo)

    if None == target_window_id:
        target_window_id = find_kdtree(active, target, allow_parent_sibling=True)

    if None == target_window_id:
        return False

    raise_window(target_window_id)
    return True


def find_kdtree(center, target, allow_parent_sibling=True):
    '''
    Adjust non-overlapping layout.
    '''
    active = center

    if None == active:
        return None

    winlist = WinList
    lay = get_current_tile(winlist, WinPosInfo)
    _tree, _map = getkdtree(winlist, lay)
    current_node = _map[active]

    if len(current_node.path) % 2 == 0:
        promote = target in ['right', 'left']
    else:
        promote = target in ['down', 'up']


    shift = -1 if target in ['left', 'up'] else 1

    promoted=False
    
    c = current_node
    if promote:
        c = c.parent
        promoted=True

    while True:
        i = c.parent.children.index(c)
        if 0 <= i + shift < len(c.parent.children):
            target = c.parent.children[i + shift]
            break
        if None == c.parent.parent or None == c.parent.parent.parent:
            return None
        c = c.parent.parent
        promoted=True

    if promoted:
        if not allow_parent_sibling:
            if not target.leaf:
                return None
    if None == target or target.overlap:
        return None
    else:
        return target.key


def minimize(wincount):
    for win in WinList:
        minimize_one(win)


def maximize(wincount):
    active = get_active_window()
    for win in WinList:
        maximize_one(win)
    raise_window(active)
    return None


def lock(_file, wait=0.5):
    t0 = 0
    if os.path.exists(_file):
        t0 = float(open(_file).read())
    t1 = time.time()
    if t1 < t0 + wait:
        return False
    f = open(_file, 'w')
    f.write(str(t1))
    f.close()
    return True


def unlock(_file):
    os.remove(_file)

def get_active_window():
    active = int(_exec_and_output("xdotool getactivewindow").split()[0])
    if active not in WinList:
        active = None
    return active

def store():
    active=get_active_window()
    if not None == active:
        h = PERSISTENT_DATA.get('active_history', [])
        h.insert(0, active)
        PERSISTENT_DATA['active_history'] = h[:1000]
    with open(config.TempFile, 'w') as f:
        PERSISTENT_DATA_ALL[Desktop] = PERSISTENT_DATA
        f.write(str(PERSISTENT_DATA_ALL))


desktop, desktop_x, desktop_y, OrigXstr, OrigYstr, MaxWidthStr, MaxHeightStr = initialize1()
WinList, WinListAll, WinPosInfo = initialize2(desktop)
Desktop = '%s,%s,%s' % (desktop, desktop_x, desktop_y)

MaxWidth = int(MaxWidthStr) - LeftPadding - RightPadding
MaxHeight = int(MaxHeightStr) - TopPadding - BottomPadding
OrigX = int(OrigXstr) + LeftPadding
OrigY = int(OrigYstr) + TopPadding

if os.path.exists(config.TempFile):
    PERSISTENT_DATA_ALL = eval(open(config.TempFile).read())
else:
    PERSISTENT_DATA_ALL = {}
PERSISTENT_DATA = PERSISTENT_DATA_ALL.get(Desktop, {})
OldWinList = PERSISTENT_DATA.get('winlist', [])

if __name__ == '__main__':
    if lock(LockFile):
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
            swap(target)
        elif arguments['move']:
            move(target)
        elif arguments['focus']:
            focus(target)

        elif arguments['layout']:
            assert not arguments['next'] == arguments['prev']
            change_tile_or_insert_new_window(shift=-1 if arguments['prev'] else 1)
        elif arguments['grow']:
            if arguments['width']:
                resize(config.RESIZE_STEP, 0)
            else:
                resize(0, config.RESIZE_STEP)
        elif arguments['shrink']:
            if arguments['width']:
                resize(-config.RESIZE_STEP, 0)
            else:
                resize(0, -config.RESIZE_STEP)

        store()

        unlock(LockFile)
