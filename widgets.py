from PySide.QtGui import *
from PySide.QtCore import *
import os
import pymel.core as pm
import utils

DEFAULT_COMMAND_BUTTON_CODE = """def clicked():
  pass
  # only the code inside clicked() will be executed
"""

DEFAULT_CHECKBOX_CODE = """def on():
  pass

def off():
  pass
  
# only the code inside on() and off() will be executed
"""

class BaseControl(QObject):
  def __init__(self):
    super(BaseControl, self).__init__()

  def move(self, pos):
    self.pos = pos
    self.widget.move(pos)

  def show(self):
    self.widget.show()

  def hide(self):
    self.widget.hide()

  # safely delete the control
  def clean_up(self):
    self.widget.hide()
    self.widget.deleteLater()
    self.deleteLater()

  def updateControl(self):
    pass


class Selector(BaseControl):
  clicked = Signal()

  def __init__(self, p, **kwargs):
    super(Selector, self).__init__()
    # define default parameters
    self.cid = kwargs.get("cid", -1) # if no cid specified set the default
    self.pos = kwargs.get("pos", QPoint(0, 0)) # if no position specified set the default
    self.color = "#FFFFFF" # default color: full white
    self.override_color = False
    self.tags = []
    self.target_objs = []
    self.tooltip = ""
    self.radius = 10
    self.is_selected = False

    self.widget = QPushButton(p) # underlying Qt widget
    self.widget.setText("") # clear the label

    # load the stylesheet for the selector
    with open(os.path.abspath(os.path.dirname(__file__)) + '\\selector.qss', 'r') as qss_file:
      self.stylesheet = qss_file.read()

    self.setup() # apply settings
    self.widget.show() 
    
    self.widget.clicked.connect(self.onWidgetTriggered)

  def colorCode(self):
    if self.override_color:
      try:
        top_obj = pm.PyNode(self.target_objs[0]) # get the first of the target objects
      except: # if target object does not exist display the warning
        pm.warning("Object {} not found. Make sure the correct scene is loaded.".format(self.target_objs[0]))
        return
      color = utils.getOverrideColor(top_obj) # set the override color (see utils.py)
      if color:
        self.color = color

  '''
  Implements the main functionality of the selector - selecting assigned objects
  '''
  def action(self, drag=False):
    appendSelection = drag or QApplication.keyboardModifiers() == Qt.ShiftModifier # selecting by dragging or shift selecting
    targetSet = set(self.target_objs) # convert to python set for convenience
    selectionSet = set(map(str, pm.ls(sl=1))) # get the object names for selected nodes and convert to set for convenience

    # if target objects are selected and appending is on
    if targetSet <= selectionSet and appendSelection: 
      pm.select(list(selectionSet - targetSet)) # remove target objects from selection leaving everything else selected
    else:
      if appendSelection: # add target objects to selection
        pm.select(self.target_objs, add=1)
      else:
        pm.select(self.target_objs) # replace current selection with target objects

  def onWidgetTriggered(self):
    self.clicked.emit()

  def redraw(self):
    radius = self.radius - 1.3 if self.is_selected else self.radius # taking the border into account
    args = {
      "color": self.color,
      "brighter": utils.brighter(self.color),
      "darker": utils.darker(self.color),
      "radius": radius,
      "double_radius": radius * 2,
      "border": 2 if self.is_selected else 0 # show 2 pixel border if the selector is activated
    }
    self.widget.setStyleSheet(self.stylesheet.format(**args)) # redraw the widget

  '''
  Returns JSON representation of the control
  '''
  def serialize(self):
    return {
    "selector" : {
        "cid": self.cid,
        "target_objs": self.target_objs,
        "color": self.color,
        "tags": self.tags,
        "override_color": self.override_color,
        "tooltip": self.tooltip,
        "pos_x": self.pos.x(),
        "pos_y": self.pos.y(),
        "radius": self.radius
      }
    }

  '''
  Loads the control from JSON representation
  '''
  def deserialize(self, json, duplicate=False):
    if not duplicate:
      self.cid = json["cid"]
      self.pos = QPoint(json["pos_x"], json["pos_y"])

    self.target_objs = json["target_objs"]
    self.color = json["color"]
    self.tags = json["tags"]
    self.override_color = json["override_color"]
    self.tooltip = json["tooltip"]
    self.radius = json.get("radius", 10)

  '''
  Apply the settings to control
  '''
  def setup(self, client=False):
    if client: # if loaded by CUI Viewer
      self.widget.setToolTip(self.tooltip)
      self.colorCode()
      self.clicked.connect(self.action)
    else:
      self.widget.setToolTip("Control ID: {}".format(self.cid)) # show cid in tooltip
    self.redraw() # redraw
    self.move(self.pos) # move into place


class CommandButton(BaseControl):
  clicked = Signal()

  def __init__(self, p, **kwargs):
    super(CommandButton, self).__init__()
    # define default parameters
    self.cid = kwargs.get("cid", -1) # if no cid specified set the default
    self.pos = kwargs.get("pos", QPoint(0, 0)) # if no position specified set the default
    self.label = "Command"
    self.cmd = DEFAULT_COMMAND_BUTTON_CODE
    self.tooltip = ""
    self.tags = []
    self.height = 20
    self.width = 60
    self.function = None
    self.parent = p
    
    self.widget = QPushButton(p)
    self.setup()
    self.widget.show()
    
    self.widget.clicked.connect(self.onWidgetTriggered)

  def onWidgetTriggered(self):
    self.clicked.emit()

  '''
  Returns JSON representation of the control
  '''
  def serialize(self):
    return {
    "command_button": {
        "cid": self.cid,
        "cmd": self.cmd,
        "label": self.label,
        "pos_x": self.pos.x(),
        "pos_y": self.pos.y(),
        "tags": self.tags,
        "height": self.height,
        "width": self.width,
        "tooltip": self.tooltip
      }
    }

  '''
  Loads the control from JSON representation
  '''
  def deserialize(self, json, duplicate=False):
    if not duplicate:
      self.cid = json["cid"]
      self.pos = QPoint(json["pos_x"], json["pos_y"])

    self.cmd = json["cmd"]
    self.label = json["label"]
    self.tags = json["tags"]
    self.height = json["height"]
    self.width = json["width"]
    self.tooltip = json["tooltip"]

  '''
  Apply the settings to control
  '''
  def setup(self, client=False):
    self.widget.resize(self.width, self.height) # set size
    self.widget.setText(self.label) # set label
    self.move(self.pos) # move into place

    if client: # if loaded by CUI Viewer
      self.widget.setToolTip(self.tooltip)
      self.clicked.connect(self.action)
    else:
      self.widget.setToolTip("Control ID: {}".format(self.cid)) # set cid as tooltip

  def action(self):
    if self.function is None: # if activating first time we need to compile the assigned code
      try:
        self.function = utils.compileFunctions(self.cmd, ["clicked"], self.parent.symbols)[0]
      except Exception: # if something went wrong display the warning
        pm.warning("Could not compile commands for this control. Please, check the code")
        return

    self.function() # run the assigned code


class Slider(BaseControl):
  valueChanged = Signal()
  released = Signal()

  def __init__(self, p, **kwargs):
    super(Slider, self).__init__()
    # setting up default settings
    self.cid = kwargs.get("cid", -1) # if no cid specified 
    self.pos = kwargs.get("pos", QPoint(0, 0)) # if no pos specified
    self.target_attr = ""
    self.min_attr_val = 0.0
    self.max_attr_val = 0.0
    self.clamp_to_int = False
    self.tags = []
    self.is_vertical = True
    self.default_val = False
    self.tooltip = ""
    self.width = 15
    self.length = 80

    self.widget = QSlider(p) # init the underlying Qt widget
    self.widget.setMaximum(100) # otherwise maximum value would be 99, which is not very nice 
    self.setup() # apply the settings
    self.widget.show()
    
    self.widget.valueChanged.connect(self.onValueChanged)
    self.widget.sliderReleased.connect(self.onReleased)

  def onValueChanged(self):
    self.valueChanged.emit()

  def onReleased(self):
    self.released.emit()

  def value(self):
    return self.widget.value()

  '''
  Sets the orientation and dimensions according to setting
  '''
  def updateGeometry(self):
    orient = Qt.Vertical if self.is_vertical else Qt.Horizontal
    self.widget.setOrientation(orient)
    if orient == Qt.Vertical:
      self.widget.resize(self.width, self.length)
    else:
      self.widget.resize(self.length, self.width)     

  '''
  Returns JSON representation of the control
  '''
  def serialize(self):
    return {
      "slider": {
        "cid": self.cid,
        "is_vertical": self.is_vertical,
        "target_attr": self.target_attr,
        "min_attr_val": self.min_attr_val,
        "max_attr_val": self.max_attr_val,
        "clamp_to_int": self.clamp_to_int,
        "pos_x": self.pos.x(),
        "pos_y": self.pos.y(),
        "tags": self.tags,
        "default_val": self.default_val,
        "tooltip": self.tooltip,
        "length": self.length
        }
    }

  '''
  Loads the control from JSON representation
  '''
  def deserialize(self, json, duplicate=False):
    if not duplicate:
      self.cid = json["cid"]
      self.pos = QPoint(json["pos_x"], json["pos_y"])

    self.is_vertical = json["is_vertical"]
    self.target_attr = json["target_attr"]
    self.min_attr_val = json["min_attr_val"]
    self.max_attr_val = json["max_attr_val"]
    self.clamp_to_int = json["clamp_to_int"]
    self.tags = json["tags"]
    self.default_val = json["default_val"]
    self.tooltip = json["tooltip"]
    self.length = json.get("length", 80)

  '''
  Apply current settings
  '''
  def setup(self, client=False):
    self.updateGeometry() # reorient
    self.move(self.pos) # move into place

    if client: # if loaded by CUI Viewer
      self.widget.setValue(self.default_val)
      self.widget.setToolTip(self.tooltip)
      self.valueChanged.connect(self.valueChangedAction)
      self.released.connect(self.releasedAction)
    else:
      self.widget.setToolTip("Control ID: {}".format(self.cid)) # set cid as tooltip

  '''
  Process the slider move event by updating the assigned attribute
  '''
  def valueChangedAction(self):
    if not self.target_attr: # if nothing assigned
      pm.warning("No attribute assigned to this slider")
      return

    range_ = self.max_attr_val - self.min_attr_val # offset between max and min
    step = range_/100 # a value per percent
    val = self.min_attr_val + self.value() * step # min + percent value * step

    if self.clamp_to_int:
      val = round(val) # round to nearest integer
    
    utils.undoable_open() # open Maya undo chunk
    pm.setAttr(self.target_attr, val) # update the attribute

  def releasedAction(self):
    utils.undoable_close() # when slider is released - free the undo chunk

  '''
  Update the control to match current attribute value
  '''
  def updateControl(self):
    range_ = self.max_attr_val - self.min_attr_val # offset between max and min
    try:
      attrVal = pm.getAttr(self.target_attr) # get the current value
    except Exception: # if attribute is not accessible or does not exist
      return

    val = (attrVal - self.min_attr_val)/(range_/100) # calculate the percent value for slider
    self.widget.blockSignals(True) # block signals to avoid the unwanted attribute update
    self.widget.setValue(round(val)) # set slider value rounding it to nearest integer
    self.widget.blockSignals(False) # unblock the signals


class CheckBox(BaseControl):
  stateChanged = Signal()

  def __init__(self, p, **kwargs):
    super(CheckBox, self).__init__()
    # set up the default settings
    self.cid = kwargs.get("cid", -1) # if no cid specified
    self.pos = kwargs.get("pos", QPoint(0, 0)) # if no pos specified
    self.cmd = DEFAULT_CHECKBOX_CODE
    self.is_dir_ctrl = True
    self.target_attr = ""
    self.default_state = False
    self.label = "Checkbox"
    self.tags = []
    self.tooltip = ""
    self.on_cmd = None
    self.off_cmd = None
    self.parent = p
    
    self.widget = QCheckBox(self.label, p) # init the underlying Qt widget
    self.setup() # apply the settings
    self.widget.show()
    
    self.widget.stateChanged.connect(self.onStateChanged)

  def isChecked(self):
    return self.widget.isChecked()
    
  def onStateChanged(self):
    self.stateChanged.emit()

  '''
  Apply current settings
  '''
  def setup(self, client=False):
    self.widget.setText(self.label) # set the label
    # resize the widget for label to fit in nicely (8px/letter, 20px for checkbox)
    self.widget.resize(len(self.label)*8+20, self.widget.height())
    self.widget.move(self.pos) # move into place
    
    if client: # if loaded by CUI Viewer
      self.widget.setToolTip(self.tooltip)
      self.widget.setChecked(self.default_state)
      self.stateChanged.connect(self.toggledAction)
    else:
      self.widget.setToolTip("Control ID: {}".format(self.cid)) # set cid as tooltip

  '''
  Process the checked/unchecked state update
  '''
  def toggledAction(self):
    if self.is_dir_ctrl: # if controling an attribute directly
      if not self.target_attr: # if no attribute assigned
        pm.warning("No attribute assigned to this checkbox")
        return
      pm.setAttr(self.target_attr, self.isChecked()) # set the boolean value for the attribute

    else: # is a command checkbox
      if not (self.on_cmd and self.off_cmd): # if commands not compiled
        try:
          funcs = utils.compileFunctions(self.cmd, ["on", "off"], self.parent.symbols)
          self.on_cmd = funcs[0] # get the on() function
          self.off_cmd = funcs[1] # get the off() function
        except Exception: # error occured while compiling
          pm.warning("Could not compile commands for this control. Please, check the code")
          return

      if self.isChecked():
        self.on_cmd() # checked => run on()
      else:
        self.off_cmd() # unchecked => run off()

  '''
  Returns the JSON representation of the control
  '''
  def serialize(self):
    return {
      "checkbox": {
        "cid": self.cid,
        "cmd": self.cmd,
        "is_dir_ctrl": self.is_dir_ctrl,
        "target_attr": self.target_attr,
        "pos_x": self.pos.x(),
        "pos_y": self.pos.y(),
        "default_state": self.default_state,
        "label": self.label,
        "tags": self.tags,
        "tooltip": self.tooltip
      }
    }

  '''
  Loads the control from JSON representation
  '''
  def deserialize(self, json, duplicate=False):
    if not duplicate:
      self.cid = json["cid"]
      self.pos = QPoint(json["pos_x"], json["pos_y"])

    self.cmd = json["cmd"]
    self.is_dir_ctrl = json["is_dir_ctrl"]
    self.target_attr = json["target_attr"]
    self.default_state = json["default_state"]
    self.label = json["label"]
    self.tags = json["tags"]
    self.tooltip = json["tooltip"]

  '''
  Update the state from Maya attribute
  '''
  def updateControl(self):
    if self.is_dir_ctrl: # if controling an attribute directly
      try:
        attrVal = pm.getAttr(self.target_attr) # get the attribute value
      except Exception: # could not reach the assigned attribute
        return
      self.widget.setChecked(attrVal) # set the state according to received value


'''
Have to subclass, because QLineEdit does not 
have any signals to be used as trigger notification
'''
class CUILineEdit(QDoubleSpinBox):
  focused = Signal()

  def __init__(self, p):
    super(CUILineEdit, self).__init__(p)
    self.setButtonSymbols(QSpinBox.NoButtons)
    self.setFocusPolicy(Qt.ClickFocus)
    self.setMinimum(-10000)
    self.setMaximum(10000)
    self.setSingleStep(0.1)

  def focusInEvent(self, event):
    if event.reason() == Qt.MouseFocusReason:
      self.focused.emit()
    else:
      event.ignore()


class FloatField(BaseControl):
  focused = Signal()

  def __init__(self, p, **kwargs):
    super(FloatField, self).__init__()
    # set up the default settings
    self.cid = kwargs.get("cid", -1) # if no cid specified
    self.pos = kwargs.get("pos", QPoint(0, 0)) # if no pos specified
    self.w = 75
    self.h = 20
    self.target_attr = ""
    self.tags = []
    self.tooltip = ""
    self.parent = p


    self.widget = CUILineEdit(p) # create the underlying Qt widget
    self.setup() # apply the settings
    self.show()
    self.widget.focused.connect(self.onFocused)

  def onFocused(self):
    self.focused.emit()

  def serialize(self):
    return {
      "float_field": {
        "cid": self.cid,
        "target_attr": self.target_attr,
        "pos_x": self.pos.x(),
        "pos_y": self.pos.y(),
        "w": self.w,
        "h": self.h,
        "tags": self.tags,
        "tooltip": self.tooltip
      }
    }

  def deserialize(self, json, duplicate=False):
    if not duplicate:
      self.cid = json["cid"]
      self.pos = QPoint(json["pos_x"], json["pos_y"])

    self.w = json["w"]
    self.h = json["h"]
    self.target_attr = json["target_attr"]
    self.tags = json["tags"]
    self.tooltip = json["tooltip"]

  def setup(self, client=False):
    self.widget.resize(self.w, self.h) # resize according to settings
    self.move(self.pos) # move into place
    if client: # if loaded by CUI Viewer
      self.widget.setToolTip(self.tooltip) # display the tooltip
      self.widget.valueChanged.connect(self.valueChangedAction)
    else:
      self.widget.setToolTip("Control ID: {}".format(self.cid)) # set cid as tooltip

  def valueChangedAction(self):
    val = self.widget.value() # convert value to float
    pm.setAttr(self.target_attr, val) # set new value to attribute

  def updateControl(self):
    try:
      val = pm.getAttr(self.target_attr) # get the attribute value
    except Exception: # abort if attribute unreachable
      return

    self.widget.setValue(val) # display new value

