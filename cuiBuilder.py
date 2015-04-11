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
    self.focusedControl = None
    self.characterName = None
    self.background = None

    self.toolbar = ui.CUIToolBar(self)

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
        if isinstance(self.focusedControl, widgets.Slider):
          self.focusedControl.is_vertical = not self.focusedControl.is_vertical
          self.focusedControl.updateGeometry()

    elif self.toolbar.checkbox.isChecked():
      self.newCheckbox(position)

    elif self.toolbar.duplicate.isChecked():
      self.duplicateControl(self.focusedControl, position)

  def mouseMoveEvent(self, event):
    lockX = QApplication.keyboardModifiers() == Qt.AltModifier
    lockY = QApplication.keyboardModifiers() == Qt.ControlModifier
    snap = QApplication.keyboardModifiers() == Qt.ShiftModifier

    if self.placingState == State.placing_new or self.placingState == State.moving:
      pos = self.mapFromGlobal(event.globalPos())-QPoint(10,10) if self.placingState == State.placing_new else event.pos()
      offset = pos - self.moveOrigin
      newPos = self.focusedControl.pos + offset
      if snap:
        nextNode = utils.nextGridNode(pos, offset, 20)
        self.focusedControl.move(nextNode)
        return

      elif lockX:
        offset.setY(0)
        newPos -= offset
      elif lockY:
        offset.setX(0)
        newPos -= offset

      self.focusedControl.move(newPos)
      self.moveOrigin = pos

  def mouseReleaseEvent(self, event):
    if self.placingState != State.idle:
      self.modified = True
    self.placingState = State.idle

  def mirrorControl(self, control):
    w = self.width()
    pos = control.pos
    mirroredPosition = QPoint(w - pos.x(), pos.y()) - QPoint(control.widget.width(), 0)
    mirroredControl = self.duplicateControl(control, mirroredPosition)

  def duplicateControl(self, control, newPos):
    copy = control.serialize()
    controlType = copy.keys()[0]

    if controlType == "selector":
      newWidget = self.newSelector(newPos)

    elif controlType == "command_button":
      newWidget = self.newCommandButton(newPos)

    elif controlType == "checkbox":
      newWidget = self.newCheckbox(newPos)

    elif controlType == "slider":
      newWidget = self.newSlider(newPos)

    newWidget.deserialize(copy[controlType], duplicate=True)
    newWidget.setup()
    return newWidget

  def onWidgetTriggered(self):
    widget = self.sender()
    self.modified = True
    self.focusedControl = widget

    if self.toolbar.mirror.isChecked():
      self.mirrorControl(widget)

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

    self.focusedControl = newSelector
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
      
    self.focusedControl = newCommandButton
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

    self.focusedControl = newSlider
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

    self.focusedControl = newCheckBox
    self.moveOrigin = pos
    self.placingState = State.placing_new
    return newCheckBox

  def save(self):
    if self.characterName is None:
      userInput = QInputDialog.getText(self, "Character Name", "Character Name")
      if userInput[1]:
        self.characterName = userInput[0]
      else:
        pm.warning("You must specify character name before saving")
        return
    
    result = QFileDialog.getSaveFileName(self, "Save", utils.charactersDir(), "CUI files (*.cui)")
    
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

  def addControl(self, control):
    self.controls[control.cid] = control

  def load(self):
    if not self.failSafe():
      return

    result = QFileDialog.getOpenFileName(self, "Open", utils.charactersDir(), "CUI files (*.cui)")
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
      controlType = ctrl.keys()[0]
      control = ctrl[controlType]

      if controlType == "selector":
        widget = widgets.Selector(self)
        widget.clicked.connect(self.onWidgetTriggered)

      elif controlType == "slider":
        widget = widgets.Slider(self)
        widget.valueChanged.connect(self.onWidgetTriggered)
        
      elif controlType == "command_button":
        widget = widgets.CommandButton(self)
        widget.clicked.connect(self.onWidgetTriggered)

      elif controlType == "checkbox":
        widget = widgets.CheckBox(self)
        widget.stateChanged.connect(self.onWidgetTriggered)

      widget.deserialize(control)
      widget.setup(client=False)
      self.addControl(widget)

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

    imagePath = utils.charactersDir()+self.background
    self.setStyleSheet("#CUIMainWindow {background-image: url(%s); background-repeat: none;}" % imagePath)
    
  def setBackground(self):
    result = QFileDialog.getOpenFileName(self, "Open", utils.charactersDir(), "Image files (*.png *jpg)")
    if not result[1]:
      return

    sourcePath = result[0]
    fileName = sourcePath.split('/')[-1]
    localPath = utils.charactersDir()+fileName

    try:
      shutil.copyfile(sourcePath, localPath)
    except Exception as e:
      pass

    self.background = fileName
    self.updateBackground()