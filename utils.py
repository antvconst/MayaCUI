import functools
import math
import pymel.core as pm
from PySide.QtCore import QPoint

'''
This block of code is responsible for maintainting
consistent UNDO-REDO stack for Maya

Chunk is an atomic sequence of commands
Undoing a chunk rolls back any commands inside
'''

CHUNK_OPEN = False # global chunk state

def undoable_open(): # opens the global chunk to store an atomic command sequence
  global CHUNK_OPEN
  if not CHUNK_OPEN:
    pm.undoInfo(ock=1)
    CHUNK_OPEN = True

def undoable_close(): # closes the global chunk
  global CHUNK_OPEN
  if CHUNK_OPEN:
    pm.undoInfo(cck=1)
    CHUNK_OPEN = False

undoable_b = functools.partial(pm.undoInfo, ock=1) # opens local chunk
undoable_e = functools.partial(pm.undoInfo, cck=1) # closes local chunk


'''
Calculates the upper left and lower right corners
of drag area specified by drag ~start~ and ~end~ positions
'''
def calculateCorners(start, end):
  offset = end - start
  if offset.x() >= 0 and offset.y() >= 0: # direction: right-down
    upper_left = start
    lower_right = end

  elif offset.x() >= 0 and offset.y() <= 0: # direction: right-up
    upper_left = QPoint(start.x(), end.y())
    lower_right = QPoint(end.x(), start.y())

  elif offset.x() <= 0 and offset.y() >= 0: # direction: left-down
    upper_left = QPoint(end.x(), start.y())
    lower_right = QPoint(start.x(), end.y())

  elif offset.x() <= 0 and offset.y() <= 0: # direction: left-up
    upper_left = end
    lower_right = start

  return (upper_left, lower_right)


'''
Wrapper for getting current project's /characters directory
'''
def charactersDir():
  rootDir = pm.workspace(q=1, rd=1)
  charDir = rootDir+"characters/"
  pm.workspace.mkdir(charDir)
  return charDir


'''
Compiles the functions inside ~string~ inside scope defined by ~symbols~
Returns only functions specified in ~names~ argument
'''
def compileFunctions(string, names, symbols):
  exec string in symbols # compile the code in given scope
  return [symbols[name] for name in names] # extract necessary functions and return them

'''
Calculates next node of the grid of ~size~ x ~size~ dimensions
In the direction of ~offset~
'''
def nextGridNode(point, offset, size):
  x = point.x()
  y = point.y()

  if offset.x() >= 0: # direction: left
    grid_x = x + (size - x % size) # clamp to nearest node on the left
  else:
    grid_x = x - x % size # clamp to nearest node on the right

  if offset.y() >= 0:
    grid_y = y + (size - y % size) # clamp to nearest node downwards
  else:
    grid_y = y - y % size # clamp to nearest node upwards

  return QPoint(grid_x, grid_y)

'''
Calculates the hex form (#XXXXXX) of the override color for ~obj~
If ~obj~ has no override color, the method traverses the hierarchy up
until one of the parents has override color in transform node.
If nothing found, None is returned
'''
def getOverrideColor(obj):
  colorId = getOverrideColorId(obj) # search for colorIndex of the obj or its parents

  if colorId:
    floatColor = pm.colorIndex(colorId, q=1) # get float RGB values from Maya for given id
    intVal = [int(math.ceil(v*255)) for v in floatColor] # convert float values to integers
    return hexColor(intVal) # convert to hex and return
  else:
    return None

'''
Recursive method to traverse hierarchy upwards looking for an override color
'''
def getOverrideColorId(obj, first_lvl=True):
  xformColor = obj.getAttr("overrideColor") # OC of the transform node
  shapeColor = obj.getShape().getAttr("overrideColor") # OC of the shape node
    
  if xformColor: # if has OC in transform
    return xformColor
  else:
    if first_lvl and shapeColor: # if we haven't yet dived into recursion and the object has OC in shape node
      return shapeColor # return it
    else:
      parentNode = obj.getParent() # get parent node
      if parentNode:
        return getOverrideColorId(parentNode, False) # start recursive traverse up the hierarchy
      else:
        return 0 # if has no parent and not own OC

'''
Returns hex form of color for given list of integer RGB values
'''
def hexColor(rgbVal):
  return "#{:02x}{:02x}{:02x}".format(*rgbVal) # using python str.format to convert RGB integers for hex

'''
Multiplies given ~color~ in hex form by ~coef~
'''
def multiplyColor(color, coef):
  r = int(coef * int(color[1]+color[2], 16))
  g = int(coef * int(color[3]+color[4], 16))
  b = int(coef * int(color[5]+color[6], 16))
    
  r = r if r<255 else 255
  g = g if g<255 else 255
  b = b if b<255 else 255
    
  return hexColor([r,g,b])

'''
Wrapper for multiplyColor to get a darker tone (0.7 coefficient)
'''
darker = lambda x: multiplyColor(x, 0.7)

'''
Wrapper for multiplyColor to get a brighter tone (1.3 coefficient)
'''
brighter = lambda x: multiplyColor(x, 1.3)