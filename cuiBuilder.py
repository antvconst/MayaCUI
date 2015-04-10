import ui
reload(ui)

import widgets
reload(widgets)

import setupDialogs 
reload(setupDialogs)
from setupDialogs import *

from PySide.QtCore import *
from PySide.QtGui import *
import json
import shutil
import utils

class State:
  idle = 0
  placing_new = 1
  moving = 2

class CUIBuilder(QDialog):
  def __init__(self):
    parent = ui.maya_main_window()
    super(CUIBuilder, self).__init__(parent)
    self.setObjectName("CUIMainWindow")
    self.setWindowTitle("Character UI Builder")
    self.setWindowFlags(Qt.Window)
    self.setAttribute(Qt.WA_DeleteOnClose)
    self.resize(512, 512)

    self.modified = False
    self.controls = {}
    self.currentCid = -1
    self.placingState = State.idle
    self.widgetUnderSetup = None
    self.characterName = None
    self.background = None

    self.toolbar = CUIToolBar(self)

    self.toolbar.save.clicked.connect(self.save)
    self.toolbar.load.clicked.connect(self.load)
    self.toolbar.background.clicked.connect(self.setBackground)

  def showEvent(self, event):
    self.toolbar.show()

  def mousePressEvent(self, event):
    position = self.mapFromGlobal(event.globalPos()-QPoint(10,10))

    if self.toolbar.move_.isChecked():
      self.placingState = State.moving
      self.moveOrigin = event.pos()

    elif self.toolbar.selector.isChecked():
      self.newSelector(position)

    elif self.toolbar.command.isChecked():
      self.newCommandButton(position)

    elif self.toolbar.slider.isChecked():
      if event.button() == Qt.LeftButton:
        self.newSlider(position)
      elif event.button() == Qt.RightButton:
        if isinstance(self.widgetUnderSetup, widgets.Slider):
          self.widgetUnderSetup.is_vertical = not self.widgetUnderSetup.is_vertical
          self.widgetUnderSetup.updateGeometry()

    elif self.toolbar.checkbox.isChecked():
      self.newCheckbox(position)

  def mouseMoveEvent(self, event):
    lockX = QApplication.keyboardModifiers() == Qt.AltModifier
    lockY = QApplication.keyboardModifiers() == Qt.ControlModifier
    snap = QApplication.keyboardModifiers() == Qt.ShiftModifier

    if self.placingState == State.placing_new or self.placingState == State.moving:
      pos = self.mapFromGlobal(event.globalPos())-QPoint(10,10) if self.placingState == State.placing_new else event.pos()
      offset = pos - self.moveOrigin
      newPos = self.widgetUnderSetup.pos + offset
      if snap:
        nextNode = utils.nextGridNode(pos, offset, 20)
        self.widgetUnderSetup.move(nextNode)
        return

      elif lockX:
        offset.setY(0)
        newPos -= offset
      elif lockY:
        offset.setX(0)
        newPos -= offset

      self.widgetUnderSetup.move(newPos)
      self.moveOrigin = pos

  def mouseReleaseEvent(self, event):
    if self.placingState != State.idle:
      self.modified = True
    self.placingState = State.idle

  def onWidgetTriggered(self):
    widget = self.sender()
    self.modified = True

    if self.toolbar.move_.isChecked():
      self.widgetUnderSetup = widget

    elif self.toolbar.mirror.isChecked():
      w = self.width()
      pos = widget.pos
      mirroredPosition = QPoint(w - pos.x(), pos.y()) - QPoint(widget.widget.width(), 0)

      if isinstance(widget, widgets.Selector):
        selector = self.newSelector()
        copy = widget.serialize()
        selector.deserialize(copy["selector"])
        selector.cid = cid
        selector.move(mirroredPosition)
        selector.setup()
      
      elif isinstance(widget, widgets.CommandButton):
        cmdButton = self.newCommandButton(mirroredPosition)
        copy = widget.serialize()
        cmdButton.deserialize(copy["command_button"])
        cmdButton.cid = cid
        cmdButton.move(mirroredPosition)
        cmdButton.setup()
      
      elif isinstance(widget, widgets.CheckBox):
        checkbox = self.newCheckbox(mirroredPosition)
        copy = widget.serialize()
        checkbox.deserialize(copy["checkbox"])
        checkbox.cid = cid
        checkbox.move(mirroredPosition)
        checkbox.setup()

      elif isinstance(widget, widgets.Slider):
        slider = self.newSlider(mirroredPosition)
        copy = widget.serialize()
        slider.deserialize(copy["slider"])
        slider.cid = cid
        slider.move(mirroredPosition)
        slider.setup()

    elif self.toolbar.setup.isChecked():
      if isinstance(widget, widgets.Selector):
        dialog = SelectorDialog(self, widget)
      
      elif isinstance(widget, widgets.CommandButton):
        dialog = CommandButtonDialog(self, widget)
      
      elif isinstance(widget, widgets.CheckBox):
        dialog = CheckBoxDialog(self, widget)

      elif isinstance(widget, widgets.Slider):
        dialog = SliderDialog(self, widget)

    elif self.toolbar.remove.isChecked():
      self.controls[widget.cid].clean_up()
      del self.controls[widget.cid]
    
  def nextCid(self):
    self.currentCid += 1
    return self.currentCid

  def newSelector(self, pos=None, cid=None):
    if pos is None:
      pos = QPoint(0, 0)

    if cid is None:
      cid = self.nextCid()

    newSelector = widgets.Selector(p=self, pos=pos, cid=cid)
    self.controls[cid] = newSelector
    newSelector.clicked.connect(self.onWidgetTriggered)

    self.widgetUnderSetup = newSelector
    self.moveOrigin = pos
    self.placingState = State.placing_new
    return newSelector

  def newCommandButton(self, pos=None, cid=None):
    if pos is None:
      pos = QPoint(0, 0)
    
    if cid is None:
      cid = self.nextCid()

    newCommandButton = widgets.CommandButton(p=self, pos=pos, cid=cid)
    self.controls[cid] = newCommandButton
    newCommandButton.clicked.connect(self.onWidgetTriggered)
      
    self.widgetUnderSetup = newCommandButton
    self.moveOrigin = pos
    self.placingState = State.placing_new
    return newCommandButton

  def newSlider(self, pos=None, cid=None):
    if pos is None:
      pos = QPoint(0, 0)

    if cid is None:
      cid = self.nextCid()

    newSlider = widgets.Slider(p=self, pos=pos, cid=cid)
    self.controls[cid] = newSlider
    newSlider.released.connect(self.onWidgetTriggered)

    self.widgetUnderSetup = newSlider
    self.moveOrigin = pos
    self.placingState = State.placing_new
    return newSlider

  def newCheckbox(self, pos=None, cid=None):
    if pos is None:
      pos = QPoint(0, 0)

    if cid is None:
      cid = self.nextCid()

    newCheckBox = widgets.CheckBox(p=self, pos=pos, cid=cid)
    self.controls[cid] = newCheckBox
    newCheckBox.stateChanged.connect(self.onWidgetTriggered)

    self.widgetUnderSetup = newCheckBox
    self.moveOrigin = pos
    self.placingState = State.placing_new
    return newCheckbox

  def save(self):
    rootDir = pm.workspace(q=1, rd=1)
    charDir = rootDir+"characters"
    pm.workspace.mkdir(charDir)
    if self.characterName is None:
      userInput = QInputDialog.getText(self, "Character Name", "Character Name")
      if userInput[1]:
        self.characterName = userInput[0]
      else:
        pm.warning("You must specify character name before saving")
        return
    
    result = QFileDialog.getSaveFileName(self, "Save", charDir, "CUI files (*.cui)")
    
    if result[1]:
      fileName = result[0]
    else:
      return

    serialized = {
      "name": self.characterName,
      "window_width": self.width(),
      "window_height": self.height(),
      "background_image": self.background,
      "last_cid": self.currentCid,
      "controls": [x.serialize() for x in self.controls.values()]
    }

    with open(fileName, "w") as outputFile:
      json.dump(serialized, outputFile)

    self.modified = False

  def load(self):
    if not self.failSafe():
      return

    rootDir = pm.workspace(q=1, rd=1)
    charDir = rootDir+"characters"
    result = QFileDialog.getOpenFileName(self, "Open", charDir, "CUI files (*.cui)")
    if result[1]:
      fileName = result[0]
    else:
      return

    with open(fileName, "r") as inputFile:
      jsonData = json.load(inputFile)

    self.resize(jsonData["window_width"], jsonData["window_height"])
    self.currentCid = jsonData["last_cid"]
    self.characterName = jsonData["name"]
    self.background = jsonData["background_image"]
    self.updateBackground()
    for ctrl in jsonData["controls"]:
      if ctrl.keys()[0] == "selector":
        selector = self.newSelector(cid=ctrl["selector"]["cid"])
        selector.deserialize(ctrl["selector"])
        selector.setup()
      elif ctrl.keys()[0] == "slider":
        slider = self.newSlider(cid=ctrl["slider"]["cid"])
        slider.deserialize(ctrl["slider"])
        slider.setup()
      elif ctrl.keys()[0] == "command_button":
        cmdButton = self.newCommandButton(cid=ctrl["command_button"]["cid"])
        cmdButton.deserialize(ctrl["command_button"])
        cmdButton.setup()
      elif ctrl.keys()[0] == "checkbox":
        checkbox = self.newCheckbox(cid=ctrl["checkbox"]["cid"])
        checkbox.deserialize(ctrl["checkbox"])
        checkbox.setup()

  def paintEvent(self, event):
    opt = QStyleOption()
    opt.initFrom(self)
    p = QPainter(self)
    self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

  def failSafe(self):
    if self.modified:
      answer = QMessageBox.question(None,
        "Unsaved changes",
        "Something has been modified since the last save.\nProceed without saving?",
        QMessageBox.Yes,
        QMessageBox.No)
      if answer == QMessageBox.Yes:
        return True
      else:
        return False
    else:
      return True

  def closeEvent(self, event):
    if not self.failSafe():
      event.ignore()
    else:
      event.accept()

  def updateBackground(self):
    if self.background is None:
      return

    rootDir = pm.workspace(q=1, rd=1)
    charDir = rootDir+"characters/"
    imagePath = charDir+self.background
    self.setStyleSheet("#CUIMainWindow {background-image: url(%s); background-repeat: none;}" % imagePath)
    
  def setBackground(self):
    rootDir = pm.workspace(q=1, rd=1)
    charDir = rootDir+"characters/"
    result = QFileDialog.getOpenFileName(self, "Open", charDir, "Image files (*.png *jpg)")
    if not result[1]:
      return

    sourcePath = result[0]
    fileName = sourcePath.split('/')[-1]
    localPath = charDir+fileName

    try:
      shutil.copyfile(sourcePath, localPath)
    except Exception as e:
      pass

    self.background = fileName
    self.updateBackground()


class CUIToolBar(QDialog):
  def __init__(self, parent):
    super(CUIToolBar, self).__init__(parent)
    
    self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
    self.setWindowTitle("Tools")

    self.setFixedSize(100, 350)
    self.layout = QVBoxLayout(self)
    self.setLayout(self.layout)
    self.grp = QButtonGroup(self)

    self.load = QToolButton(self)
    self.load.setText("Load")
    self.layout.addWidget(self.load)
    self.load.setMinimumSize(80, 25)

    self.save = QToolButton(self)
    self.save.setText("Save")
    self.layout.addWidget(self.save)
    self.save.setMinimumSize(80, 25)

    self.background = QToolButton(self)
    self.background.setText("Set BG")
    self.layout.addWidget(self.background)
    self.background.setMinimumSize(80, 25)

    self.idle = QToolButton(self)
    self.idle.setCheckable(True)
    self.idle.setChecked(True)
    self.idle.setText("Idle")
    self.layout.addWidget(self.idle)
    self.idle.setMinimumSize(80, 25)

    self.move_ = QToolButton(self)
    self.move_.setCheckable(True)
    self.move_.setText("Move")
    self.layout.addWidget(self.move_)
    self.move_.setMinimumSize(80, 25)

    self.remove = QToolButton(self)
    self.remove.setCheckable(True)
    self.remove.setText("Remove")
    self.layout.addWidget(self.remove)
    self.remove.setMinimumSize(80, 25)
    
    self.mirror = QToolButton(self)
    self.mirror.setCheckable(True)
    self.mirror.setText("Mirror")
    self.layout.addWidget(self.mirror)
    self.mirror.setMinimumSize(80, 25)

    self.setup = QToolButton(self)
    self.setup.setCheckable(True)
    self.setup.setText("Setup")
    self.layout.addWidget(self.setup)
    self.setup.setMinimumSize(80, 25)

    self.selector = QToolButton(self)
    self.selector.setCheckable(True)
    self.selector.setText("Selector")
    self.layout.addWidget(self.selector)
    self.selector.setMinimumSize(80, 25)

    self.checkbox = QToolButton(self)
    self.checkbox.setCheckable(True)
    self.checkbox.setText("Checkbox")
    self.layout.addWidget(self.checkbox)
    self.checkbox.setMinimumSize(80, 25)

    self.slider = QToolButton(self)
    self.slider.setCheckable(True)
    self.slider.setText("Slider")
    self.layout.addWidget(self.slider)
    self.slider.setMinimumSize(80, 25)
    
    self.command = QToolButton(self)
    self.command.setCheckable(True)
    self.command.setText("Command")
    self.layout.addWidget(self.command)
    self.command.setMinimumSize(80, 25)
    
    self.grp.addButton(self.move_)
    self.grp.addButton(self.checkbox)
    self.grp.addButton(self.command)
    self.grp.addButton(self.setup)
    self.grp.addButton(self.selector)
    self.grp.addButton(self.slider)
    self.grp.addButton(self.mirror)
    self.grp.addButton(self.remove)
    self.grp.addButton(self.idle)
    self.grp.setExclusive(True)