"""Keep translation sources on widgets so a language change updates them live."""
from PySide6 import QtWidgets as W
from i18n import Text, tr, remember


class Localized:
    def __init__(self, *args, **kwargs):
        values = list(args)
        initial = values[0] if values and isinstance(values[0], Text) else None
        if initial is not None:
            values[0] = str(initial)
        super().__init__(*values, **kwargs)
        if initial is not None:
            remember(self, 'setText', initial)

    def retranslate(self):
        for setter, value in list(getattr(self, '_localized_text', {}).items()):
            if isinstance(setter, tuple):
                name, index = setter
                if name == 'setHorizontalHeaderLabels':
                    getattr(super(), name)([str(label) for label in value])
                else:
                    getattr(super(), name)(index, str(value))
            else:
                getattr(super(), setter)(str(value))
        self.updateGeometry()

    def _set(self, setter, value):
        remember(self, setter, value)
        getattr(super(), setter)(str(value))

    def setText(self, value): self._set('setText', value)
    def setToolTip(self, value): self._set('setToolTip', value)
    def setPlaceholderText(self, value): self._set('setPlaceholderText', value)
    def setWindowTitle(self, value): self._set('setWindowTitle', value)
    def setSuffix(self, value): self._set('setSuffix', value)
    def setLabelText(self, value): self._set('setLabelText', value)
    def setCancelButtonText(self, value): self._set('setCancelButtonText', value)
    def setHtml(self, value): self._set('setHtml', value)
    def setPlainText(self, value): self._set('setPlainText', value)


class QLabel(Localized, W.QLabel): pass
class QPushButton(Localized, W.QPushButton): pass
class QCheckBox(Localized, W.QCheckBox): pass
class QLineEdit(Localized, W.QLineEdit): pass
class QPlainTextEdit(Localized, W.QPlainTextEdit): pass
class QTextBrowser(Localized, W.QTextBrowser): pass
class QSpinBox(Localized, W.QSpinBox): pass
class QDialog(Localized, W.QDialog): pass
class QMainWindow(Localized, W.QMainWindow): pass
class QProgressDialog(Localized, W.QProgressDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if args and isinstance(args[0], Text):
            self._localized_text.pop('setText', None)
            remember(self, 'setLabelText', args[0])
        if len(args) > 1 and isinstance(args[1], Text):
            remember(self, 'setCancelButtonText', args[1])


class QComboBox(Localized, W.QComboBox):
    def addItem(self, text, userData=None):
        index = self.count()
        super().addItem(str(text), userData)
        remember(self, ('setItemText', index), text)

    def addItems(self, texts):
        for text in texts:
            self.addItem(text)


class QTableWidget(Localized, W.QTableWidget):
    def setHorizontalHeaderLabels(self, labels):
        super().setHorizontalHeaderLabels([str(label) for label in labels])
        if any(isinstance(label, Text) for label in labels):
            remember(self, ('setHorizontalHeaderLabels', None), tr(''))
            self._localized_text[('setHorizontalHeaderLabels', None)] = list(labels)


class QFileDialog(W.QFileDialog):
    @staticmethod
    def getOpenFileNames(*args, **kwargs):
        kwargs['options'] = kwargs.get('options', W.QFileDialog.Option(0)) | W.QFileDialog.Option.DontUseNativeDialog
        return W.QFileDialog.getOpenFileNames(*args, **kwargs)

    @staticmethod
    def getSaveFileName(*args, **kwargs):
        kwargs['options'] = kwargs.get('options', W.QFileDialog.Option(0)) | W.QFileDialog.Option.DontUseNativeDialog
        return W.QFileDialog.getSaveFileName(*args, **kwargs)
