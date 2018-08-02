# Liwei He  u5817287



import math
import random
from time import clock


def build_a_map(size , cut):
    list_node = []
    for i in range(0, size):

        # (x,y)
        list_node.append((random.random()* 10, random.random()* 10))
    if cut == 1:
        size = int(3*size/4)
        list_node = list_node[:size]
    if cut == 2:
        size = int(size/2)
        list_node = list_node[:size]
    if cut == 3:
        size = int(size/4)
        list_node = list_node[:size]

    # form the matrix
    distance_matrix = [[[]for i in range(size)] for i in range(size)]
    for x in range(size):
        for y in range(size):
            distance_matrix[x][y] = weight_calculation(list_node[x], list_node[y])

    return distance_matrix, size


def weight_calculation(node_1, node_2):
    weight = math.sqrt(math.pow(node_1[0] - node_2[0], 2) + math.pow(node_1[1] - node_2[1], 2))

    return weight

def heapfy(priority_queue, index):

    old_index = index
    is_modified = False
    max_index = priority_queue.__len__()

    # shift down
    while index * 2 +1 < max_index :
        if priority_queue[index][0] > priority_queue[index * 2 +1][0]:
            internal = priority_queue[index * 2 + 1]
            priority_queue[index * 2 + 1] = priority_queue[index]
            priority_queue[index] = internal
            is_modified = True


        if (index*2 + 2) != max_index:
            if priority_queue[index][0] > priority_queue[index * 2 + 2][0]:
                internal = priority_queue[index * 2 + 2]
                priority_queue[index * 2 + 2] = priority_queue[index]
                priority_queue[index] = internal
                index = index * 2 + 2
                is_modified = True
            else:
                index = index * 2 + 1
        else:
            index = index*2 + 1

    # if there is no change being made then shift up
    if is_modified == False:
        while old_index >= 0:

            if priority_queue[old_index][0] < priority_queue[int((old_index - 1) / 2)][0]:
                internal = priority_queue[int((old_index - 1) / 2)]
                priority_queue[int((old_index - 1) / 2)] = priority_queue[old_index]
                priority_queue[old_index] = internal
                old_index = int((old_index - 1) / 2)
            else:
                old_index = -1
    return priority_queue



# "size" is the number of node in the original graph, "i" is a fraction size of original graph
def form_mst(size, i):

    total_weight = 0

    # store the min spaning tree
    MST = []

    # create a matrix of a randomly generated complete graph
    matrix, size = build_a_map(size, i)

    start = clock()

    # initialize the priority queue
    priority_queue = []
    for x in range (size):
        # initialize the priority_queue with the all node (min_distance, node_index)
        priority_queue.append([100, x])

    # randomly choose a node
    start_node = 0

    MST.append(start_node)

    # find the min_weight node for connected node
    for x in range(priority_queue.__len__()):
        min_weight = matrix[start_node][x]
        node = x
        priority_queue[x] = [min_weight,node]
        heapfy(priority_queue, x)


    while len(MST) < size:
        # pop up from priority queue
        new_node = priority_queue[0]

        weight = new_node[0]
        total_weight += weight

        # heapify the priority queue
        priority_queue[0] = priority_queue.pop()
        if len(priority_queue) > 1:
            heapfy(priority_queue, 0)

        MST.append(new_node[1])

        # update the min_weight of all connected nodes in priority queue
        for x in range(priority_queue.__len__()):
            current_node = priority_queue[x][1]
            if matrix[new_node[1]][current_node] < priority_queue[x][0]:
                min_weight = matrix[new_node[1]][current_node]

                priority_queue[x][0] = min_weight
                heapfy(priority_queue, x)

    finish = clock()

    return total_weight, finish - start

# main procedure
for size in (200, 400, 800, 1600):
    number_of_test = 20
    average = []
    for v in range(0,4):
        total_weight = 0
        total_time = 0
        for i in range(number_of_test):
            weight, time = form_mst(size, v)
            total_weight += weight
            total_time += time

        average.append( total_weight/number_of_test)

        if v == 0:
            print("Average edge weights of ", size ," nodes is ", average[v], ", needs time: ", total_time)

        else:
            print("the ratio of the sum of the edge weights of the MST of V ", v , "is ", average[v]/average[0])



