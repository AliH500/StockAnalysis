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
    return tree

def build_min(index,low,high,tree,arr):
    if low == high:
        tree[index] = arr[low]
        return
    mid = (low + high)//2
    build_min(2*index+1,low,mid) #Common storing technique of storing left portion to 2*index+1 position
    build_min(2*index+2,mid,high) #Common storing technique of storing right portion to 2*index+2 position
    tree[index] = min(tree[index*2+1],tree[index*2+2]) #The index's value is the minimum of its     left and right half values
    return tree

def build_sum(index,low,high,tree,arr):
    if low == high:
        tree[index] = arr[low]
        return
    mid = (low + high)//2
    build_sum(2*index+1,low,mid) #Common storing technique of storing left portion to 2*index+1 position
    build_sum(2*index+2,mid,high) #Common storing technique of storing right portion to 2*index+2 position
    tree[index] = sum(tree[index*2+1],tree[index*2+2]) #The index's value is the minimum of its left and right half values
    return tree

def query_max(index,low,high,l,r,tree):
    #l and r are the range provided by the user
    #low and high is the range that the current tree[index] is responsible for
    min_value = -1*(10**20)
    
    if low >= l and high <= r: #Full Overlap
        return tree[index]
    
    if high<l or low>r:  #No overlap
        return min_value
    
    #Partial Overlap
    mid = (low+high)//2
    left = query_max(2*index+1,low,mid,l,r,tree)
    right = query_max(2*index+2,mid+1,high,l,r,tree)
    return max(left,right) 

def query_min(index,low,high,l,r,tree):
    #l and r are the range provided by the user
    #low and high is the range that the current tree[index] is responsible for
    max_value = 1*(10**20)
    
    if low >= l and high <= r: #Full Overlap
        return tree[index]
    
    if high<l or low>r: #No overlap
        return max_value
    
    #Partial Overlap
    mid = (low+high)//2
    left = query_min(2*index+1,low,mid,l,r,tree)
    right = query_min(2*index+2,mid+1,high,l,r,tree)
    return min(left,right)

def query_sum(index,low,high,l,r,tree):
    #l and r are the range provided by the user
    #low and high is the range that the current tree[index] is responsible for
    
    if low >= l and high <= r: #Full Overlap
        return tree[index]
    
    if high<l or low>r: #No overlap
        return 0
    
    #Partial Overlap
    mid = (low+high)//2
    left = query_sum(2*index+1,low,mid,l,r,tree)
    right = query_sum(2*index+2,mid+1,high,l,r,tree)
    return sum(left,right)