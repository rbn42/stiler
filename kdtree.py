#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from divide import divide

def kdtree(_input,path=None,treemap=None,parentmeta=None,parent=None):
    if None==treemap:
        #root
        treemap={}
        path=[]

    node=Node()
    node.parent=parent
    node.path=path
    depth=len(path)

    if len(_input)<2:
        node.leaf=True
        node.overlap=False
        node.content=_input
        node.key=_input[0][1]
    else:

        _input2=[[pos[depth%2],pos[depth%2+2]] for pos,_,_ in _input] #column first
        children=divide(zip(_input2,_input))

        if len(children)<2 and depth>0:
            node.leaf=True
            node.overlap=True
            node.content=_input
        else:   

            node.leaf=False
            node.children=[]
            for child,i in zip(children,range(len(children))):
                children_path=path+[i]
                _list=[i[1] for i in child]
                
                node_child=kdtree(_list,path=children_path,treemap=treemap,parent=node)
                node.children.append(node_child)

                if node_child.overlap:
                    node.overlap=True

    if node.leaf:
        for _,key,pos in node.content:
            treemap[key]=node
        children_pos=[pos for _,key,pos in node.content]
    else:
        children_pos=[_child.position for _child in node.children]

    minx,miny=10**6,10**6
    maxx,maxy=-10**6,-10**6
    for pos in children_pos:
        minx=min(minx,pos[0])
        miny=min(miny,pos[1])
        maxx=max(maxx,pos[2])
        maxy=max(maxy,pos[3])
    node.position=[minx,miny,maxx,maxy]

    if 0==depth:
        return node,treemap
    else:
        return node

class Node:
    parent=None
    path=None
    children=None
    key=None
    leaf=None
    overlap=None
    position=None
    content=None
    modified=False
    def __str__(self):
        msg=self.path,self.leaf,self.overlap,self.position,self.content,
        return ",".join([str(i) for i in msg])

def regularize(node,border):
    x0,y0,x1,y1=node.position
    depth=len(node.path)
    if node.leaf:
        return
    for child in node.children: 
        if len(node.path)%2==0:
            child.position[1],child.position[3]=y0,y1
        else:   
            child.position[0],child.position[2]=x0,x1
    if len(node.path)%2==0:
        i0,i1,b=x0,x1,border[0]
        index0,index1=0,2
    else:
        i0,i1,b=y0,y1,border[1]
        index0,index1=1,3
    i0=i0-b
    size=i1-i0 - len(node.children) *b
    size_sum=0
    for child in node.children: 
        if child.modified:
            size-=child.position[index1]-child.position[index0]
        else:
            size_sum+=child.position[index1]-child.position[index0]
    print(size)
    print(size_sum)

    i=i0
    for child in node.children:
        i+=b
        _size=child.position[index1]-child.position[index0]
        if not child.modified:
            _size=_size*size/size_sum
            _size=int(_size)
        child.position[index0]=i
        i+=_size
        child.position[index1]=i

    for child in node.children: 
        regularize(child,border)
    return 
    

def getLayoutAndKey(node,result=None,min_width=50,min_height=50):
    if None==result:
        result=[],[]
    if node.leaf:
        x0,y0,x1,y1 =node.position
        if x1-x0<min_width or y1-y0<min_height:
            #error
            a=1/0
        layout=[x0,y0,x1-x0,y1-y0] 
        result[0].append(layout)
        result[1].append(node.key)
    else:
        for child in node.children:
            getLayoutAndKey(child,result)
    return result


