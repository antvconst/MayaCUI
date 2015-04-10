import functools
import math
import pymel.core as pm

CHUNK_OPEN = False

def undoable_open():
  global CHUNK_OPEN
  if not CHUNK_OPEN:
    pm.undoInfo(ock=1)
    CHUNK_OPEN = True

def undoable_close():
  global CHUNK_OPEN
  if CHUNK_OPEN:
    pm.undoInfo(cck=1)
    CHUNK_OPEN = False

undoable_b = functools.partial(pm.undoInfo, ock=1)
undoable_e = functools.partial(pm.undoInfo, cck=1)

def compileFunctions(string, names, symbols):
  exec string in symbols
  return [symbols[name] for name in names]


def nextGridNode(point, offset, size):
  x = point.x()
  y = point.y()

  if offset.x() >= 0:
    grid_x = x + (size - x % size)
  else:
    grid_x = x - x % size 

  if offset.y() >= 0:
    grid_y = y + (size - y % size)
  else:
    grid_y = y - y % size

  return QPoint(grid_x, grid_y)

def getOverrideColor(obj):
  colorId = getOverrideColorId(obj)

  if colorId:
    floatColor = pm.colorIndex(colorId, q=1)
    intVal = [int(math.ceil(v*255)) for v in floatColor]
    return hexColor(intVal)
  else:
    return None

def getOverrideColorId(obj, first_lvl=True):
  xformColor = obj.getAttr("overrideColor")
  shapeColor = obj.getShape().getAttr("overrideColor")
    
  if xformColor:
    return xformColor
  else:
    if first_lvl and shapeColor:
      return shapeColor                
    else:
      parentNode = obj.getParent()
      if parentNode:
        return getOverrideColorId(parentNode, False)
      else:
        return 0

def hexColor(rgbVal):
  return "#{:02x}{:02x}{:02x}".format(*rgbVal)

def multiplyColor(color, coef):
  r = int(coef * int(color[1]+color[2], 16))
  g = int(coef * int(color[3]+color[4], 16))
  b = int(coef * int(color[5]+color[6], 16))
    
  r = r if r<255 else 255
  g = g if g<255 else 255
  b = b if b<255 else 255
    
  return hexColor([r,g,b])

darker = lambda x: multiplyColor(x, 0.7)
brighter = lambda x: multiplyColor(x, 1.3)