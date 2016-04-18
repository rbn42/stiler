#! /usr/bin/python 
# -*- coding: UTF-8 -*-
# A set of python utility functions using pyxlib to get information about
# windows and desktop
import sys
import os

from Xlib import X, display, Xutil, Xatom, xobject

MAX_PROPERTY_VALUE_LEN = 4096

# Query a window for an Atom property
def get_property(window, prop_name, type):
  xa_prop_name = window.display.get_atom(prop_name)
  return window.get_property(xa_prop_name, type, 0, MAX_PROPERTY_VALUE_LEN)

# Get a Window object from a wid
def get_window(display, wid):
  cls = display.get_resource_class('window', xobject.drawable.Window)
  return cls(display, wid, owner = 1)

from Xlib import xobject
def get_parent_absolute_position(win):
    x,y=0,0
    while True:
        try:
            pwin=win.query_tree().parent
            g=pwin.get_geometry()
            x+=g.x
            y+=g.y
        except:
            break
        win=pwin
    return x,y

def moveandresize(wid,x,y,w,h):
  disp = display.Display()
  root_win = disp.screen().root
  disp,wid=root_win.display,wid
  win=xobject.drawable.Window(disp,wid)
  win.configure(x=x,y=y,width=w,height=h)
  win.get_geometry()
def flush(wid):
  disp = display.Display()
  root_win = disp.screen().root
  disp,wid=root_win.display,wid
  win=xobject.drawable.Window(disp,wid)
  win.get_geometry()
def get_active_window():
  disp = display.Display()
  root_win = disp.screen().root
  win = get_property(root_win, "_NET_ACTIVE_WINDOW", Xatom.WINDOW)
  disp,wid=root_win.display,win.value[0]
  window = get_window(disp, wid)
  win=xobject.drawable.Window(disp,wid)
  win.configure(width=800)
  win.get_geometry()
  return window
  return new_window_from_wid(root_win.display, win.value[0])

# Information (name, geometry) about a window
class WindowInfo:
  def __init__(self, window, desktop):
    self.id = window.id
    self.name = window.get_wm_name()
    g = window.get_geometry()
    self.x = g.x
    self.y = g.y
    self.width = g.width
    self.height = g.height
    self.border = g.border_width
    #self.state = window.get_wm_state()['state']
    self.visible = window.get_wm_state()['state'] == Xutil.NormalState
    # using map_state only return visible windows on current desktop
    #self.viewable = window.get_attributes().map_state == X.IsViewable
    self.desktop = desktop

  def __str__(self):
    return "[%i vis=%i, desk=%i, pos=(%i,%i) size=(%i,%i) border=%i, '%s']"%(
        self.id, self.visible, self.desktop, self.x, self.y, 
        self.width, self.height, self.border, self.name)

# Create a WindowInfo from a window id
def new_window_from_wid(disp, wid):
  window = get_window(disp, wid)
  desktop = get_property(window, "_NET_WM_DESKTOP", Xatom.CARDINAL).value[0]
  if desktop == 0xFFFFFFFF: #special case : should appear on all
    desktop = -1

  return WindowInfo(window, desktop)
 
# Return a list of top-level [WindowInfo]
def get_windows():
  disp = display.Display()
  root_win = disp.screen().root
  win_list = get_property(root_win, "_NET_CLIENT_LIST", Xatom.WINDOW)
  num_desks = get_property(root_win, "_NET_NUMBER_OF_DESKTOPS", Xatom.CARDINAL).value[0]
  win_infos = {}

  for i in range(num_desks):
    win_infos[i] = []

  for wid in win_list.value:
    w = new_window_from_wid(root_win.display, wid)
    if w.desktop != -1:
      win_infos[w.desktop].append(w)

  return win_infos

def get_root_win():
  disp = display.Display()
  root_win = disp.screen().root
  return root_win


def get_current_desktop():
  disp = display.Display()
  root_win = disp.screen().root
  d = get_property(root_win, "_NET_CURRENT_DESKTOP", Xatom.CARDINAL)
  return d.value[0]

# Geometry information for desktop
class DesktopInfo:
  def __init__(self, width, height):
    self.width = width
    self.height = height

  def __str__(self):
    return "[w=%i, h=%i]"%(self.width, self.height)

# Returns a DesktopInfo describing the desktop setup
def get_desktop_geom():
  disp = display.Display()
  root_win = disp.screen().root
  desktop_geom = get_property(root_win, "_NET_DESKTOP_GEOMETRY", Xatom.CARDINAL)
  width = desktop_geom.value[0]
  height = desktop_geom.value[1]
  return DesktopInfo(width, height)


if __name__ == '__main__':
  windows = get_windows()
  print "Found following windows :"
  for desk in windows:
    print "--- Desktop %i"%desk
    for w in windows[desk]:
      print w
  print "---"

  desktop = get_desktop_geom()
  print desktop

  print "current_desktop : %i"%get_current_desktop()


disp = display.Display()
root_win = disp.screen().root

def get_active_window():
  win = get_property(root_win, "_NET_ACTIVE_WINDOW", Xatom.WINDOW)
  return win.value[0]

def get_position_and_size(winid):
  window = get_window(root_win.display, winid)
  px,py=get_parent_absolute_position(window)
  g=window.get_geometry()
  return [g.x+px,g.y+py,g.width,g.height]
def get_shift():
    win=get_active_window()
    pos1=xutils.get_position_and_size(win)
    xutils.moveandresize(win,*pos1)
    pos2=xutils.get_position_and_size(win)
