import bpy

def getNeighbors(obj):
    # TODO: Find objects next to obj
    return [obj]

def findBestNeighbor(obj):
    neighbors = getNeighbors(obj)
    if len(neighbors) == 0:
        return None
    elif len(neighbors) == 1:
        return neighbors[0]
    else:
        # TODO: Write code to get best neighbor from list
        return None

def merge(objs):
    for obj in objs:
        bestNeighbor = None
        while not bestNeighbor:
            bestNeighbor = findBestNeighbor(obj):
