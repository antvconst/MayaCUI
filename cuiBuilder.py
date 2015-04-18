from . import DEBUG

import ui
import widgets
import setupDialogs 
import utils

if DEBUG:
  reload(ui)
  reload(widgets)
  reload(setupDialogs)
  reload(utils)

from setupDialogs import *
from PySide.QtCore import *
from PySide.QtGui import *
import json
import shutil


class State: # enum for widget placing states
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

    self.modified = False
    self.controls = {}
    self.currentCid = -1
    self.placingState = State.idle
    self.focusedControl = None
    self.characterName = None
    self.background = None

    self.reset()
    self.toolbar = ui.CUIToolBar(self)

    self.toolbar.save.clicked.connect(self.save)
    self.toolbar.load.clicked.connect(self.load)
    self.toolbar.background.clicked.connect(self.setBackground)

  def showEvent(self, event):
    self.toolbar.show()

  '''
  Process mouse down event
  '''
  def mousePressEvent(self, event):
    self.setFocus()

    # get the position of click
    position = self.mapFromGlobal(event.globalPos()-QPoint(10,10))

    if self.toolbar.move_.isChecked(): # if move tool is active
      self.placingState = State.moving
      self.moveOrigin = event.pos()

    elif self.toolbar.selector.isChecked(): # if selector tool is active
      self.newSelector(position) # create a new selector

    elif self.toolbar.command.isChecked(): # if command button tool is active
      self.newCommandButton(position) # create a new command button

    elif self.toolbar.slider.isChecked(): # if slider tool is active
      if event.button() == Qt.LeftButton:
        self.newSlider(position) # left button => create new slider
      elif event.button() == Qt.RightButton: # right button => reorient the active slider
        if isinstance(self.focusedControl, widgets.Slider):
          self.focusedControl.is_vertical = not self.focusedControl.is_vertical
          self.focusedControl.updateGeometry()

    elif self.toolbar.checkbox.isChecked(): # if checkbox tool is active
      self.newCheckbox(position) # create a new checkbox

    elif self.toolbar.floatField.isChecked(): # if float field tool is active
      self.newFloatField(position) # create a new float field

    elif self.toolbar.duplicate.isChecked(): # if duplicate tool is acive
      self.duplicateControl(self.focusedControl, position) # duplicate the focused control

  '''
  Process mouse move event
  '''
  def mouseMoveEvent(self, event):
    lockX = QApplication.keyboardModifiers() == Qt.AltModifier # Alt => locking X
    lockY = QApplication.keyboardModifiers() == Qt.ControlModifier # Ctrl => locking Y
    snap = QApplication.keyboardModifiers() == Qt.ShiftModifier # Shift => snapping to grid

    if self.placingState == State.placing_new or self.placingState == State.moving: # if not idle
      # get the possition according to state
      pos = self.mapFromGlobal(event.globalPos())-QPoint(10,10) if self.placingState == State.placing_new else event.pos()
      offset = pos - self.moveOrigin # calculate offset from origin
      newPos = self.focusedControl.pos + offset # naive calculate new position
      if snap: # if snapping to grid
        nextNode = utils.nextGridNode(pos, offset, 20) # get next node in the offset direction
        self.focusedControl.move(nextNode) # move the focused control
        return # exit

      elif lockX: # if locking X
        offset.setY(0) 
        newPos -= offset # zero out X offset
      elif lockY: # if locking Y
        offset.setX(0)
        newPos -= offset # zero out Y offset

      self.focusedControl.move(newPos) # move the control into new position
      self.moveOrigin = pos # set the new move origin

  '''
  Process mouse release event
  '''
  def mouseReleaseEvent(self, event):
    if self.placingState != State.idle:
      self.modified = True # do not let the user exit without saving
    self.placingState = State.idle # clear the state

  '''
  Horizontally mirrors the specified control
  '''
  def mirrorControl(self, control):
    w = self.width()
    pos = control.pos
    mirroredPosition = QPoint(w - pos.x(), pos.y()) - QPoint(control.widget.width(), 0)
    mirroredControl = self.duplicateControl(control, mirroredPosition)

  '''
  Create a duplicate of given control in given position
  '''
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

    elif controlType == "float_field":
      newWidget = self.newFloatField(newPos)

    newWidget.deserialize(copy[controlType], duplicate=True)
    newWidget.setup()
    return newWidget

  def onWidgetTriggered(self):
    widget = self.sender() # get the triggered control
    self.modified = True # do not let the user exit without saving
    self.focusedControl = widget # update focus

    if self.toolbar.mirror.isChecked(): # mirror tool active => mirror the control
      self.mirrorControl(widget)

    elif self.toolbar.setup.isChecked(): # setup tool active => show setup dialog
      if isinstance(widget, widgets.Selector): # for selector
        dialog = SelectorDialog(self, widget)
      
      elif isinstance(widget, widgets.CommandButton): # for command button
        dialog = CommandButtonDialog(self, widget)
      
      elif isinstance(widget, widgets.CheckBox): # for checkbox
        dialog = CheckBoxDialog(self, widget)

      elif isinstance(widget, widgets.Slider): # for slider
        dialog = SliderDialog(self, widget)

      elif isinstance(widget, widgets.FloatField): # for float field
        dialog = FloatFieldDialog(self, widget)

    elif self.toolbar.remove.isChecked(): # remove tool active => destroy the control
      self.controls[widget.cid].clean_up()
      del self.controls[widget.cid]
    
  '''
  Get next unique control id
  '''
  def nextCid(self):
    self.currentCid += 1
    return self.currentCid

  '''
  Create new selector
  '''
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

  '''
  Create new command button
  '''
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

  '''
  Create new slider
  '''
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

  '''
  Create new checkbox
  '''
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

  '''
  Create new float field
  '''
  def newFloatField(self, pos=None, cid=None):
    if pos is None:
      pos = QPoint(0, 0)

    if cid is None:
      cid = self.nextCid()

    newFloatField = widgets.FloatField(p=self, pos=pos, cid=cid)
    self.controls[cid] = newFloatField
    newFloatField.focused.connect(self.onWidgetTriggered)

    self.focusedControl = newFloatField
    self.moveOrigin = pos
    self.placingState = State.placing_new
    return newFloatField

  '''
  Save the current layout to file
  '''
  def save(self):
    if self.characterName is None:
      # ask for character name (appears as tab title in CUI Viewer)
      userInput = QInputDialog.getText(self, "Character Name", "Character Name")
      if userInput[1]:
        self.characterName = userInput[0]
      else:
        pm.warning("You must specify character name before saving")
        return
    
    # request filename to save the layout
    result = QFileDialog.getSaveFileName(self, "Save", utils.charactersDir(), "CUI files (*.cui)")
    
    if result[1]:
      fileName = result[0]
    else:
      return # about if no file selected

    serialized = {
      "name": self.characterName,
      "window_width": self.width(),
      "window_height": self.height(),
      "background_image": self.background,
      "last_cid": self.currentCid,
      "controls": [x.serialize() for x in self.controls.values()] # serialize all controls
    }

    with open(fileName, "w") as outputFile:
      json.dump(serialized, outputFile) # write the JSON data into specified file

    self.modified = False # clear the modification state

  def addControl(self, control):
    self.controls[control.cid] = control

  '''
  Load the layout from file
  '''
  def load(self):
    if not self.failSafe(): # trying to exit without saving
      return

    # request the filename
    result = QFileDialog.getOpenFileName(self, "Open", utils.charactersDir(), "CUI files (*.cui)")
    if result[1]:
      fileName = result[0]
    else:
      return # abort if not file specified

    self.reset()

    with open(fileName, "r") as inputFile:
      jsonData = json.load(inputFile) # parse JSON data

    self.resize(jsonData["window_width"], jsonData["window_height"])
    self.currentCid = jsonData["last_cid"]
    self.characterName = jsonData["name"]
    self.background = jsonData["background_image"]
    self.updateBackground()

    for ctrl in jsonData["controls"]: # load the controls
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

      elif controlType == "float_field":
        widget = widgets.FloatField(self)
        widget.focused.connect(self.onWidgetTriggered)

      widget.deserialize(control)
      widget.setup(client=False)
      self.addControl(widget)

  '''
  Without this stylesheets will not work (Qt peculiarity)
  '''
  def paintEvent(self, event):
    opt = QStyleOption()
    opt.initFrom(self)
    p = QPainter(self)
    self.style().drawPrimitive(QStyle.PE_Widget, opt, p, self)

  '''
  Check if user tries to exit without saving changes and show the confirmation dialog
  '''
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
      event.ignore() # abort if exit without changes not confirmed
    else:
      event.accept() # otherwise exit

  '''
  Redraw the background
  '''
  def updateBackground(self):
    if self.background is None:
      self.setStyleSheet("#CUIMainWindow {}")
      return

    imagePath = utils.charactersDir()+self.background # get path
    # set the stylesheet
    self.setStyleSheet("#CUIMainWindow {background-image: url(%s); background-repeat: none;}" % imagePath)
    
  def setBackground(self):
    # request the PNG/JPG file to be used as BG
    result = QFileDialog.getOpenFileName(self, "Open", utils.charactersDir(), "Image files (*.png *jpg)")
    if not result[1]:
      return

    sourcePath = result[0]
    fileName = sourcePath.split('/')[-1] # cut filename out of the absolute path
    localPath = utils.charactersDir()+fileName # format the path to store the BG image

    try:
      shutil.copyfile(sourcePath, localPath) # copy the BG image to /characters folder of the project
    except Exception as e:
      pass # if already exists

    self.background = fileName # set the BG filename
    self.updateBackground() # redraw the BG

  def reset(self):
    self.resize(512, 512)
    self.modified = False
    if self.controls:
      for control in self.controls.values():
        control.clean_up()
    self.controls = {}
    self.currentCid = -1
    self.placingState = State.idle
    self.focusedControl = None
    self.characterName = None
    self.background = None
    self.updateBackground()