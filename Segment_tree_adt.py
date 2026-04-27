#Citation1 : https://www.youtube.com/watch?v=-dUiRtJ8ot0
#Citation2 : https://www.youtube.com/watch?v=I7RFycpqbDk&t
from math import ceil,log2,inf
from Segmenttree_testcases import *
def create_tree(arr):
    n = len(arr)
    hieght = ceil(log2(n))
    n_nodes = 2*(2**hieght) - 1
    tree = []
    for i in range(n_nodes):
        tree.append(None)
    return tree


def build_max(index,low,high,tree,arr):
    if low == high:
        tree[index] = arr[low] #when one elem remains
        return
    mid = (low + high)//2
    build_max(2*index+1,low,mid,tree,arr) #Common storing technique of storing left portion to 2*index+1 position
    build_max(2*index+2,mid+1,high,tree,arr) #Common storing technique of storing right portion to 2*index+2 position
    tree[index] = max(tree[index*2+1],tree[index*2+2]) #The index's value is the maximum of its left and right half values
    return tree #index*2+1=left child, index*2+2=right child

def build_min(index,low,high,tree,arr):
    if low == high:
        tree[index] = arr[low] #when one elem remains
        return
    mid = (low + high)//2
    build_min(2*index+1,low,mid,tree,arr) #Common storing technique of storing left portion to 2*index+1 position
    build_min(2*index+2,mid+1,high,tree,arr) #Common storing technique of storing right portion to 2*index+2 position
    tree[index] = min(tree[index*2+1],tree[index*2+2]) #The index's value is the minimum of its left and right half values
    return tree

def build_sum(index,low,high,tree,arr):
    if low == high:
        tree[index] = arr[low]
        return
    mid = (low + high)//2
    build_sum(2*index+1,low,mid,tree,arr) #Common storing technique of storing left portion to 2*index+1 position
    build_sum(2*index+2,mid+1,high,tree,arr) #Common storing technique of storing right portion to 2*index+2 position
    tree[index] = tree[index*2+1]+tree[index*2+2] #The index's value is the sum of its left and right half values
    return tree

def query_max(index,low,high,l,r,tree):
    #l and r are the range provided by the user
    #low and high is the range that the current tree[index] is responsible for
    # min_value = -1*(10**20)
    min_value = -inf
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
    max_value = inf
    
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
    return left+right

def get_range(index, low, high, l, r, max_tree, min_tree): #Returns the range (max - min) for a given query range [l, r]


    # Get max value in range
    max_value = query_max(index, low, high, l, r, max_tree)

    # Get min value in range
    min_value = query_min(index, low, high, l, r, min_tree)

    # Range = max - min
    return max_value - min_value

def get_mean(index, low, high, l, r, sum_tree): #Returns the mean (average) for a given query range [l, r]


    # Get sum of values in range
    sum_value = query_sum(index, low, high, l, r, sum_tree)

    # Number of elements in range
    n = (r - l) + 1   #right index - left index + 1 (since both indices are inclusive)

    # Safety check (avoid division by zero)
    if n <= 0:
        return 0

    # Mean = sum / number of elements
    return sum_value / n


def get_IQR(arr, l, r): #Returns the Interquartile Range (IQR) for a given range [l, r]


    sub = arr[l:r+1]

    if len(sub) == 0:
        return 0

    sub.sort()
    n = len(sub)

    q1_index = int(0.25 * (n - 1)) #q1 is the value at 25th percentile, which is at index 0.25*(n-1) in the sorted array
    q3_index = int(0.75 * (n - 1)) #q3 is the value at 75th percentile, which is at index 0.75*(n-1) in the sorted array

    return sub[q3_index] - sub[q1_index]