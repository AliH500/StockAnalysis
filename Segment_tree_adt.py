#Citation : https://www.youtube.com/watch?v=-dUiRtJ8ot0
from math import ceil,log2

def build_max(index,low,high,tree,arr):
    if low == high:
        tree[index] = arr[low]
        return
    mid = (low + high)//2
    build_max(2*index+1,low,mid) #Common storing technique of storing left portion to 2*index+1 position
    build_max(2*index+2,mid,high) #Common storing technique of storing right portion to 2*index+2 position
    tree[index] = max(tree[index*2+1],tree[index*2+2]) #The index's value is the maximum of its left and right half values

def build_min(index,low,high,tree,arr):
    if low == high:
        tree[index] = arr[low]
        return
    mid = (low + high)//2
    build_min(2*index+1,low,mid) #Common storing technique of storing left portion to 2*index+1 position
    build_min(2*index+2,mid,high) #Common storing technique of storing right portion to 2*index+2 position
    tree[index] = min(tree[index*2+1],tree[index*2+2]) #The index's value is the minimum of its left and right half values

def build_sum(index,low,high,tree,arr):
    if low == high:
        tree[index] = arr[low]
        return
    mid = (low + high)//2
    build_sum(2*index+1,low,mid) #Common storing technique of storing left portion to 2*index+1 position
    build_sum(2*index+2,mid,high) #Common storing technique of storing right portion to 2*index+2 position
    tree[index] = sum(tree[index*2+1],tree[index*2+2]) #The index's value is the minimum of its left and right half values
    