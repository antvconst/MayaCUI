import cuiViewer
import cuiBuilder

BUILDER_INSTANCE = None # global builder instance
VIEWER_INSTANCES = [] # collection of global viewer instances

def builder(): # show the builder
  global BUILDER_INSTANCE
  reload(cuiBuilder)
  BUILDER_INSTANCE = cuiBuilder.CUIBuilder()
  BUILDER_INSTANCE.show()

def viewer(tab=None): # show the viewer
  global VIEWER_INSTANCES
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