这是在stiler.py的基础上修改的仿i3-wm的窗口导航工具

依赖
=
```bash
sudo apt install python-docopt -y
```

可用的指令
=

见
```bash
python stiler.py -h
```

推荐的键盘映射
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

这里有一份从unity7中备份的配置
[org.gnome.settings-daemon.plugins.media-keys](https://github.com/rbn42/home/blob/master/config/dconf/org.gnome.settings-daemon.plugins.media-keys)

Layout
=
可用的Layout方面暂时没有设置成可配置选项.  
我预设了几个个人觉得比较顺手的窗口布局,通过`stiler.py layout next`切换.  
如果你需要不同的布局,请查找关键词:`TILES:可选的布局模式`调整源代码.也可以通过编写一个类似`get_simple_tile`的函数添加新的窗口布局.
