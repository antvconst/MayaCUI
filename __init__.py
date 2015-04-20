BUILDER_INSTANCE = None # global builder instance
VIEWER_INSTANCES = [] # collection of global viewer instances
DEBUG = False

import cuiViewer
import cuiBuilder

def builder(dbg=False): # show the builder
  global BUILDER_INSTANCE, DEBUG

  if dbg:
    DEBUG = True
    reload(cuiBuilder)

  BUILDER_INSTANCE = cuiBuilder.CUIBuilder()
  BUILDER_INSTANCE.show()

def viewer(tab=None, dbg=False): # show the viewer
  global VIEWER_INSTANCES, DEBUG
  
  if dbg:
    DEBUG = True
    reload(cuiViewer)
  
  new_instance = cuiViewer.CUIViewer(tab)
  VIEWER_INSTANCES.append(new_instance)
  new_instance.show()

def kill(): # kill everything
  global BUILDER_INSTANCE, VIEWER_INSTANCES

  if BUILDER_INSTANCE:
    BUILDER_INSTANCE.close()
    BUILDER_INSTANCE.deleteLater()
    BUILDER_INSTANCE = None

  if VIEWER_INSTANCES:
    for instance in VIEWER_INSTANCES:
      instance.deleteLater()