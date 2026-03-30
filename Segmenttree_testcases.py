from Segment_tree_adt import *
#    0   1  2   3  4   5  6   7   8   9   10  11  12
a = [10, 9, 14, 5, 12, 3, 15, 21, 32, 51, 12, 14, 5]

#Build the max tree 
tree1 = []
build_max(0,0,len(a)-1,tree1,a)
#verify that the max from a[3:10] is 51
