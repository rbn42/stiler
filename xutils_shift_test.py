import xutils
current=xutils.get_active_window()
pos=xutils.get_position_and_size(current)
print(pos)
xutils.moveandresize(current,*pos)
pos=xutils.get_position_and_size(current)
print(pos)
