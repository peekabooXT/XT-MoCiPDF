"""Offline UI catalogs; document text and personal definitions are never translated."""
import json
import sys
import weakref
import re
from pathlib import Path

LANGUAGES = [('en', 'English'), ('zh-CN', '简体中文'), ('de', 'Deutsch'),
             ('ja', '日本語'), ('fr', 'Français'), ('ko', '한국어'),
             ('it', 'Italiano'), ('hi', 'हिन्दी'), ('es', 'Español'),
             ('ar', 'العربية الفصحى'), ('pt', 'Português'), ('ru', 'Русский')]
_language = 'en'
_catalogs = {}
_widgets = weakref.WeakSet()
_qt_translator = None


def catalog(code):
    if code not in _catalogs:
        assets = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent.parent))
        path = assets / 'locales' / (code + '.json')
        _catalogs[code] = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    return _catalogs[code]


def current_language():
    return _language


def font_families():
    primary = {'hi':'Noto Sans Devanagari', 'ar':'Noto Sans Arabic',
               'ja':'Noto Sans JP', 'ko':'Noto Sans KR'}.get(_language, 'Microsoft YaHei')
    return list(dict.fromkeys([primary, 'Microsoft YaHei', 'Noto Sans KR', 'Noto Sans JP',
                              'Noto Sans Devanagari', 'Noto Sans Arabic', 'Arial', 'Segoe UI']))


class Text(str):
    def __new__(cls, parts):
        value = cls.render_parts(parts)
        instance = super().__new__(cls, value)
        instance.parts = tuple(parts)
        return instance

    @staticmethod
    def render_parts(parts):
        output = []
        for part in parts:
            if isinstance(part, tuple):
                source, params = part
                value = source if _language == 'zh-CN' else catalog(_language).get(source, catalog('en').get(source, source))
                if params:
                    value = value.format(**{key: str(item) if isinstance(item, Text) else item for key, item in params.items()})
                output.append(value)
            else:
                output.append(str(part))
        return ''.join(output)

    def __str__(self):
        return self.render_parts(self.parts)

    def __add__(self, other):
        return Text(self.parts + (other.parts if isinstance(other, Text) else (str(other),)))

    def __radd__(self, other):
        return Text((other.parts if isinstance(other, Text) else (str(other),)) + self.parts)


def tr(source, **params):
    if isinstance(source, Text) and not params:
        return Text(source.parts)
    return Text(((source, params),))


def remember(widget, property_name, value):
    if isinstance(value, Text):
        if not hasattr(widget, '_localized_text'):
            widget._localized_text = {}
        widget._localized_text[property_name] = value
        _widgets.add(widget)
    elif hasattr(widget, '_localized_text'):
        widget._localized_text.pop(property_name, None)


def set_language(code, app=None):
    global _language, _qt_translator
    if code not in dict(LANGUAGES):
        raise ValueError('Unsupported interface language')
    catalog(code)  # Validate resource before changing live state.
    _language = code
    if app:
        from PySide6.QtCore import Qt, QTranslator, QLibraryInfo
        from PySide6.QtGui import QFont
        font = QFont()
        font.setFamilies(font_families())
        font.setPointSize(10)
        app.setFont(font)
        css_families = ', '.join('"' + family + '"' for family in font_families())
        app.setStyleSheet(re.sub(r'font-family:[^;]+;', 'font-family: ' + css_families + ';', app.styleSheet()))
        if _qt_translator:
            app.removeTranslator(_qt_translator)

        class InterfaceTranslator(QTranslator):
            def isEmpty(self):
                return False

            def translate(self, context, source, disambiguation=None, n=-1):
                # None denotes "no translation" to Qt. An empty string is a
                # real empty translation and can invalidate names such as A4.
                value = catalog(_language).get('qt:' + source) or super().translate(context, source, disambiguation, n)
                return value or None

        _qt_translator = InterfaceTranslator(app)
        # Qt translations cover native dialog/navigation text; our catalog
        # supplies the common controls when Qt has no catalog (e.g. Hindi).
        _qt_translator.load('qtbase_' + ('zh_CN' if code == 'zh-CN' else code),
                            QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath))
        app.installTranslator(_qt_translator)
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft if code == 'ar' else Qt.LayoutDirection.LeftToRight)
    import shiboken6
    for widget in list(_widgets):
        if shiboken6.isValid(widget):
            widget.retranslate()


def load_language(state):
    code = state.get('language', 'en')
    return code if code in dict(LANGUAGES) else 'en'
