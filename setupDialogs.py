import ui
from ui import Ui_commandButtonDialog, Ui_selectorDialog, Ui_sliderDialog, Ui_checkboxDialog

from PySide.QtGui import QDialog, QApplication, QInputDialog
from PySide.QtCore import Qt

import pymel.core as pm

'''
Returns the user's choice of one of the attributes of the first selected object
'''
def queryAttributeChoice(parentDialog):
  objName = str(pm.ls(sl=1)[0]) # getting the first selected object

  if QApplication.keyboardModifiers() == Qt.ControlModifier:
    attrs = pm.listAttr(objName, w=1) # Ctrl pressed => showing all writeable channels
  elif QApplication.keyboardModifiers() == Qt.AltModifier:
    attrs = pm.listAttr(objName, ud=1) # Alt pressed => showing only user defined channels
  else:
    attrs = pm.listAttr(objName, k=1) # otherwise showing only keyable channels

  choice = QInputDialog.getItem(parentDialog, "Attributes", "Choose an attribute to be driven", attrs)
  if choice[1]:
    return "{obj}.{attr}".format(obj=objName, attr=choice[0]) # formatting the full attribute name
  else: # if no choice has been made (window closed etc)
    return None

'''
The following class definitions implement simple logic behind the control setup dialogs
Everything should be straight-forward, no need in further comments
'''
class CommandButtonDialog(QDialog, Ui_commandButtonDialog):
  def __init__(self, parent, widget):
    super(CommandButtonDialog, self).__init__(parent)
    self.setupUi(self)
    self.show()

    self.widget = widget
    self.labelEdit.setText(widget.label)
    self.tooltipEdit.setText(widget.tooltip)
    self.heightSpin.setValue(widget.height)
    self.widthSpin.setValue(widget.width)
    if widget.tags:
      self.tagsEdit.setText(" ".join(widget.tags))
    
    self.codeEdit.setPlainText(widget.cmd)

    self.saveButton.clicked.connect(self.save)
    self.closeButton.clicked.connect(self.close)

  def save(self):
    self.widget.label = self.labelEdit.text()
    self.widget.tooltip = self.tooltipEdit.text()
    self.widget.height = self.heightSpin.value()
    self.widget.width = self.widthSpin.value()
    self.widget.cmd = self.codeEdit.toPlainText()
    self.widget.tags = self.tagsEdit.text().split()
    self.widget.setup()
    self.close()

class SelectorDialog(QDialog, Ui_selectorDialog):
  def __init__(self, parent, widget):
    super(SelectorDialog, self).__init__(parent)
    self.setupUi(self)
    self.show()

    self.widget = widget
    self.colorEdit.setText(widget.color)
    self.radiusSpin.setValue(widget.radius)
    self.colorCheckbox.setChecked(widget.override_color)
    if widget.tags:
      self.tagsEdit.setText(" ".join(widget.tags))

    if widget.target_objs:
      for obj in widget.target_objs:
        self.targetList.addItem(obj)

    self.tooltipEdit.setText(widget.tooltip)

    self.saveButton.clicked.connect(self.save)
    self.closeButton.clicked.connect(self.close)
    self.loadButton.clicked.connect(self.updateList)

  def updateList(self):
    selection = [str(i) for i in pm.ls(sl=1)]
    self.targetList.clear()
    for obj in selection:
      self.targetList.addItem(obj)

  def save(self):
    self.widget.override_color = self.colorCheckbox.isChecked()
    self.widget.color = self.colorEdit.text()
    self.widget.tags = self.tagsEdit.text().split()
    self.widget.target_objs = self.get_target_objs()
    self.widget.tooltip = self.tooltipEdit.text()
    self.widget.radius = self.radiusSpin.value()
    self.widget.redraw()
    self.close()

  def get_target_objs(self):
    cnt = self.targetList.count()
    return [self.targetList.item(i).text() for i in range(cnt)]

class SliderDialog(QDialog, Ui_sliderDialog):
  def __init__(self, parent, widget):
    super(SliderDialog, self).__init__(parent)
    self.setupUi(self)
    self.show()

    self.widget = widget
    self.attributeEdit.setText(widget.target_attr)
    self.defaultValueSpin.setValue(widget.default_val)
    self.minValueSpin.setValue(widget.min_attr_val)
    self.maxValueSpin.setValue(widget.max_attr_val)
    self.clampToIntCheckbox.setChecked(widget.clamp_to_int)
    self.tooltipEdit.setText(widget.tooltip)
    self.lengthSpin.setValue(widget.length)
    if widget.tags:
      self.tagsEdit.setText(" ".join(widget.tags))

    self.saveButton.clicked.connect(self.save)
    self.closeButton.clicked.connect(self.close)
    self.loadButton.clicked.connect(self.loadObj)

  def save(self):
    self.widget.target_attr = self.attributeEdit.text()
    self.widget.default_val = self.defaultValueSpin.value()
    self.widget.min_attr_val = self.minValueSpin.value()
    self.widget.max_attr_val = self.maxValueSpin.value()
    self.widget.clamp_to_int = self.clampToIntCheckbox.isChecked()
    self.widget.tags = self.tagsEdit.text().split()
    self.widget.tooltip = self.tooltipEdit.text()
    self.widget.length = self.lengthSpin.value()
    self.widget.setup()
    self.close()

  def loadObj(self):
    attribute = queryAttributeChoice(self)
    if attribute:
      self.attributeEdit.setText(attribute)


class CheckBoxDialog(QDialog, Ui_checkboxDialog):
  def __init__(self, parent, widget):
    super(CheckBoxDialog, self).__init__(parent)
    self.setupUi(self)
    self.show()

    self.widget = widget
    self.codeEdit.setPlainText(widget.cmd)
    self.defaultStateCheckbox.setChecked(widget.default_state)
    self.labelEdit.setText(widget.label)
    self.attributeEdit.setText(widget.target_attr)

    if widget.tags:
      self.tagsEdit.setText(" ".join(widget.tags))
    
    if widget.is_dir_ctrl:
      self.directControlRadio.toggle()
      self.set_direct_control_mode()
    else:
      self.scriptRadio.toggle()
      self.set_script_mode()

    self.directControlRadio.toggled.connect(self.set_direct_control_mode)
    self.scriptRadio.toggled.connect(self.set_script_mode)
    self.saveButton.clicked.connect(self.save)
    self.closeButton.clicked.connect(self.close)
    self.loadButton.clicked.connect(self.loadObj)

  def set_direct_control_mode(self):
    self.attributeEdit.setEnabled(True)
    self.loadButton.setEnabled(True)
    self.codeEdit.setEnabled(False)

  def set_script_mode(self):
    self.attributeEdit.setEnabled(False)
    self.loadButton.setEnabled(False)
    self.codeEdit.setEnabled(True)

  def save(self):
    self.widget.cmd = self.codeEdit.toPlainText()
    self.widget.label = self.labelEdit.text()
    self.widget.target_attr = self.attributeEdit.text()
    self.widget.tags = self.tagsEdit.text().split()
    self.widget.default_state = self.defaultStateCheckbox.isChecked()
    self.widget.is_dir_ctrl = self.directControlRadio.isChecked()
    self.widget.setup()
    self.close()

  def loadObj(self):
    attribute = queryAttributeChoice(self)
    if attribute:
      self.attributeEdit.setText(attribute)


class FloatFieldDialog(QDialog, ui.Ui_floatFieldDialog):
  def __init__(self, parent, widget):
    super(FloatFieldDialog, self).__init__(parent)
    self.setupUi(self)

    self.widget = widget
    self.tagsEdit.setText("".join(widget.tags))
    self.attributeEdit.setText(widget.target_attr)
    self.tooltipEdit.setText(widget.tooltip)
    self.widthSpin.setValue(widget.w)
    self.heightSpin.setValue(widget.h)

    self.loadButton.clicked.connect(self.loadObj)
    self.saveButton.clicked.connect(self.save)
    self.closeButton.clicked.connect(self.close)

    self.show()

  def loadObj(self):
    attribute = queryAttributeChoice(self)
    if attribute:
      self.attributeEdit.setText(attribute)

  def save(self):
    self.widget.tags = self.tagsEdit.text().split()
    self.widget.target_attr = self.attributeEdit.text()
    self.widget.tooltip = self.tooltipEdit.text()
    self.widget.h = self.heightSpin.value()
    self.widget.w = self.widthSpin.value()
    self.widget.setup()
    self.close()