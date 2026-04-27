
# #    0   1  2   3  4   5  6   7   8   9   10  11  12
# a = [10, 9, 14, 5, 12, 3, 15, 21, 32, 51, 12, 14, 5]

# #Build the max tree 
# tree1 = []
# print(build_max(0,0,len(a)-1,tree1,a))
# #verify that the max from a[3:10] is 51
from Segment_tree_adt import create_tree, build_max, build_min, build_sum, query_max, query_min, query_sum, get_mean, get_range, get_IQR


# ---------- Helper Function ----------
def run_all_tests(arr):
    print("\n==============================")
    print("Input Array:", arr)

    if arr is None:
        print("Invalid input")
        return

    if len(arr) == 0:
        print("Edge Case: Empty array")
        return

    n = len(arr)

    # Create trees
    max_tree = create_tree(arr)
    min_tree = create_tree(arr)
    sum_tree = create_tree(arr)

    # Build trees
    build_max(0, 0, n-1, max_tree, arr)
    build_min(0, 0, n-1, min_tree, arr)
    build_sum(0, 0, n-1, sum_tree, arr)

    # Full range query
    print("\nFull Range [0, n-1]:")
    print("Max:", query_max(0,0,n-1,0,n-1,max_tree))
    print("Min:", query_min(0,0,n-1,0,n-1,min_tree))
    print("Sum:", query_sum(0,0,n-1,0,n-1,sum_tree))

    #newly added functions for mean, range and IQR
    print("Mean:", get_mean(0,0,n-1,0,n-1,sum_tree))
    print("Range:", get_range(0,0,n-1,0,n-1,max_tree,min_tree))
    print("IQR:", get_IQR(arr, 0, n-1))


    # Partial Range Query
    l = int(input("\nEnter left index for partial range query: "))
    r = int(input("Enter right index for partial range query: "))

    #validation of user input for partial range query
    if r >= n:
        print("Invalid range. Right index exceeds array length")
        return
    if l < 0:
        print("Invalid range. Left index cannot be negative")
        return
    if l > r:
        print("Invalid range. Left index cannot be greater than right index")
        return

    print("\nPartial Range [", l, ",", r, "]:")
    print("Max:", query_max(0,0,n-1,l,r,max_tree))
    print("Min:", query_min(0,0,n-1,l,r,min_tree))
    print("Sum:", query_sum(0,0,n-1,l,r,sum_tree))

    print("Mean:", get_mean(0,0,n-1,l,r,sum_tree))
    print("Range:", get_range(0,0,n-1,l,r,max_tree,min_tree))
    print("IQR:", get_IQR(arr, l, r))
# User input function to allow testing with custom data
def get_user_input():
    user_input = input("\nEnter numeric data separated by space (or press Enter to skip): ")

    if user_input == "":
        return []

    parts = user_input.split()
    arr = []

    for x in parts:
        arr.append(int(x))   

    return arr


# ---------- TEST CASES ----------

# 1. Basic first testing sample used
run_all_tests([10, 9, 14, 5, 12, 3, 15, 21, 32, 51, 12, 14, 5])

# 2. Single element
run_all_tests([7])

# 3. All equal values
run_all_tests([5, 5, 5, 5])

# 4. Negative values
run_all_tests([-10, -5, -20, -3])

# 5. Mixed values
run_all_tests([3, -1, 7, 0, -5, 8])

# 6. Empty array
run_all_tests([])

# 7. User input
user_arr = get_user_input()
run_all_tests(user_arr)

# 8. Large input performance test
run_all_tests(list(range(1000)))