#!/usr/bin/env python

import os
import signal
from gi.repository import Gtk as gtk
from gi.repository import AppIndicator3 as appindicator


def main():
    indicator = appindicator.Indicator.new(
        'w-cycle', "application-default-icon", appindicator.IndicatorCategory.SYSTEM_SERVICES)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(gtk.Menu())
    indicator.connect("scroll-event", scroll)
    gtk.main()


def scroll(aai, ind, steps):
    if steps == steps.DOWN:
        os.system('python ~/bin/stiler.py cycle')
    elif steps==steps.UP:
        os.system('python ~/bin/stiler.py anticycle')

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    main()
