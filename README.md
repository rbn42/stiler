This is a window tiling and navigation tool based on wmctrl and xdotool. I tried to imitate the very basic functions of i3-wm.

Dependencies
=
```bash
sudo apt install python-docopt -y
```

Commands
=

see
```bash
python stiler.py -h
```

Recommended Keyboard Mapping
=

| Keys      | Command   |
| ------------- |-------------| 
|`<Super> <Space>`    |  `python stiler.py layout next` |
|`<Super> <Shift> <Space>`    |  `python stiler.py layout prev` |
|`<Super> h`    |  `python stiler.py focus left` |
|`<Super> <Shift> h`    |  `python stiler.py swap left` |
|`<Super> j`    |  `python stiler.py focus down` |
|`<Super> <Shift> j`    |  `python stiler.py swap down` |
|`<Super> k`    |  `python stiler.py focus up` |
|`<Super> <Shift> k`    |  `python stiler.py swap up` |
|`<Super> l`    |  `python stiler.py focus right` |
|`<Super> <Shift> l`    |  `python stiler.py swap right` |

Here is a configuration file dumped for Unity7:
[org.gnome.settings-daemon.plugins.media-keys](https://github.com/rbn42/home/blob/master/config/dconf/org.gnome.settings-daemon.plugins.media-keys)

