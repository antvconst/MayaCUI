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
    self.cid = kwargs.get("cid", -1)
    self.pos = kwargs.get("pos", QPoint(0, 0))
    self.color = "#FFFFFF"
    self.override_color = False
    self.tags = []
    self.target_objs = []
    self.tooltip = ""
    self.radius = 10

    self.widget = QPushButton(p)
    self.widget.setToolTip("Control ID: {}".format(self.cid))
    self.widget.setText("")

    with open(os.path.abspath(os.path.dirname(__file__)) + '\\selector.qss', 'r') as qss_file:
      self.stylesheet = qss_file.read()

    self.setup()
    self.widget.show()
    
    self.widget.clicked.connect(self.onWidgetTriggered)

  def colorCode(self):
    if self.override_color:
      try:
        top_obj = pm.PyNode(self.target_objs[0])
      except:
        pm.warning("Object {} not found. Make sure the correct scene is loaded.".format(self.target_objs[0]))
        return
      color = utils.getOverrideColor(top_obj)
      if color:
        self.color = color

  def action(self):
    if QApplication.keyboardModifiers() == Qt.ShiftModifier:
      pm.select(self.target_objs, add=1)
    else:
      pm.select(self.target_objs)

  def onWidgetTriggered(self):
    self.clicked.emit()

  def redraw(self):
    args = {
      "color": self.color,
      "brighter": utils.brighter(self.color),
      "darker": utils.darker(self.color),
      "radius": self.radius,
      "double_radius": self.radius * 2,
    }
    self.widget.setStyleSheet(self.stylesheet.format(**args))

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

  def setup(self, client=False):
    if client:
      self.widget.setToolTip(self.tooltip)
      self.colorCode()
      self.clicked.connect(self.action)
      
    self.redraw()
    self.move(self.pos)


class CommandButton(BaseControl):
  clicked = Signal()

  def __init__(self, p, **kwargs):
    super(CommandButton, self).__init__()
    self.cid = kwargs.get("cid", -1)
    self.pos = kwargs.get("pos", QPoint(0, 0))
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
    self.widget.setToolTip("Control ID: {}".format(self.cid))
    self.widget.show()
    
    self.widget.clicked.connect(self.onWidgetTriggered)

  def onWidgetTriggered(self):
    self.clicked.emit()

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

  def setup(self, client=False):
    self.widget.resize(self.width, self.height)
    self.widget.setText(self.label)
    self.move(self.pos)

    if client:
      self.widget.setToolTip(self.tooltip)
      self.clicked.connect(self.action)

  def action(self):
    if self.function is None:
      try:
        self.function = utils.compileFunctions(self.cmd, ["clicked"], self.parent.symbols)[0]
      except Exception:
        pm.warning("Could not compile commands for this control. Please, check the code")
        return

    self.function()


class Slider(BaseControl):
  valueChanged = Signal()
  released = Signal()

  def __init__(self, p, **kwargs):
    super(Slider, self).__init__()
    self.cid = kwargs.get("cid", -1)
    self.pos = kwargs.get("pos", QPoint(0, 0))
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

    self.widget = QSlider(p)
    self.widget.setMaximum(100)
    self.widget.setToolTip("Control ID: {}".format(self.cid))
    self.setup()
    self.widget.show()
    
    self.widget.valueChanged.connect(self.onValueChanged)
    self.widget.sliderReleased.connect(self.onReleased)

  def onValueChanged(self):
    self.valueChanged.emit()

  def onReleased(self):
    self.released.emit()

  def value(self):
    return self.widget.value()

  def updateGeometry(self):
    orient = Qt.Vertical if self.is_vertical else Qt.Horizontal
    self.widget.setOrientation(orient)
    if orient == Qt.Vertical:
      self.widget.resize(self.width, self.length)
    else:
      self.widget.resize(self.length, self.width)     

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

  def setup(self, client=False):
    self.updateGeometry()
    self.move(self.pos)

    if client:
      self.widget.setValue(self.default_val)
      self.widget.setToolTip(self.tooltip)
      self.valueChanged.connect(self.valueChangedAction)
      self.released.connect(self.releasedAction)

  def valueChangedAction(self):
    if not self.target_attr:
      pm.warning("No attribute assigned to this slider")
      return

    range_ = self.max_attr_val - self.min_attr_val
    step = range_/100
    val = self.min_attr_val + self.value() * step

    if self.clamp_to_int:
      val = round(val)
    
    utils.undoable_open()
    pm.setAttr(self.target_attr, val)

  def releasedAction(self):
    utils.undoable_close()

  def updateControl(self):
    range_ = self.max_attr_val - self.min_attr_val
    attrVal = pm.getAttr(self.target_attr)
    val = (attrVal - self.min_attr_val)/(range_/100)
    self.widget.blockSignals(True)
    self.widget.setValue(round(val))
    self.widget.blockSignals(False)


class CheckBox(BaseControl):
  stateChanged = Signal()

  def __init__(self, p, **kwargs):
    super(CheckBox, self).__init__()
    self.cid = kwargs.get("cid", -1)
    self.pos = kwargs.get("pos", QPoint(0, 0))
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
    
    self.widget = QCheckBox(self.label, p)
    self.widget.setToolTip("Control ID: {}".format(self.cid))
    self.setup()
    self.widget.show()
    
    self.widget.stateChanged.connect(self.onStateChanged)

  def isChecked(self):
    return self.widget.isChecked()
    
  def onStateChanged(self):
    self.stateChanged.emit()

  def setup(self, client=False):
    self.widget.setText(self.label)
    self.widget.resize(len(self.label)*8+20, self.widget.height())
    self.widget.move(self.pos)
    
    if client:
      self.widget.setToolTip(self.tooltip)
      self.widget.setChecked(self.default_state)
      self.stateChanged.connect(self.toggledAction)

  def toggledAction(self):
    if self.is_dir_ctrl:
      if not self.target_attr:
        pm.warning("No attribute assigned to this checkbox")
        return
      pm.setAttr(self.target_attr, self.isChecked())

    else:
      if not (self.on_cmd and self.off_cmd):
        try:
          funcs = utils.compileFunctions(self.cmd, ["on", "off"], self.parent.symbols)
          self.on_cmd = funcs[0]
          self.off_cmd = funcs[1]
        except Exception:
          pm.warning("Could not compile commands for this control. Please, check the code")
          return

      if self.isChecked():
        self.on_cmd()
      else:
        self.off_cmd()

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

  def updateControl(self):
    if self.is_dir_ctrl:
      attrVal = pm.getAttr(self.target_attr)
      self.widget.setChecked(attrVal)