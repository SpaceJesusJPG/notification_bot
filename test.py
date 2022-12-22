from functools import reduce

readings = [10, 5, 15, 20, 12]
lowest = reduce(lambda x, y: x if x < y else y, readings)
print(lowest)
