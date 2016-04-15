#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# This code is an example for a tutorial on Ubuntu Unity/Gnome AppIndicators:
# http://candidtim.github.io/appindicator/2014/09/13/ubuntu-appindicator-step-by-step.html

import os
import signal
import json

from urllib2 import Request, urlopen, URLError

from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator
from gi.repository import Notify as notify


APPINDICATOR_ID = 'indicator-rofi'


def main():
    indicator = appindicator.Indicator.new(APPINDICATOR_ID,"window-list", appindicator.IndicatorCategory.SYSTEM_SERVICES)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(build_menu())
    indicator.connect("scroll-event", scroll)
    notify.init(APPINDICATOR_ID)
    gtk.main()

def scroll(aai, ind, steps):
#    print(steps==gtk.GdkScrollDirection)
    if steps==steps.DOWN:
        os.system('python ~/bin/stiler.py layout next')
    else:
        os.system('python ~/bin/stiler.py layout prev')
    #rofi()
#    print "hello" # doesn't print anything

def build_menu():
    menu = gtk.Menu()
    return menu
    item_joke = gtk.MenuItem('rofi')
    item_joke.connect('activate', joke)
    menu.append(item_joke)
    item_quit = gtk.MenuItem('Quit')
    item_quit.connect('activate', quit)
    menu.append(item_quit)
    menu.show_all()
    return menu

def fetch_joke():
    request = Request('http://api.icndb.com/jokes/random?limitTo=[nerdy]')
    response = urlopen(request)
    joke = json.loads(response.read())['value']['joke']
    return joke

def joke(_):
    rofi()
#    notify.Notification.new("<b>Joke</b>", "j", None).show()
    #notify.Notification.new("<b>Joke</b>", fetch_joke(), None).show()

def quit(_):
    notify.uninit()
    gtk.main_quit()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
