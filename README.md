# XT 阅迹 · XT-ReadTrace

[English](README.md) | [简体中文](README.zh-CN.md) | [Deutsch](README.de.md) | [日本語](README.ja.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [Italiano](README.it.md) | [हिन्दी](README.hi.md) | [Español](README.es.md) | [العربية الفصحى](README.ar.md) | [Português](README.pt.md) | [Русский](README.ru.md)

**1.14.0** — Notes: type directly on the PDF page, press Ctrl+Enter to save or Esc to cancel. Drag a saved note to move it; double-click to edit. The top timer supports start, pause and reset; elapsed time is restored paused after reopening. All exports, including multi-file merging, are in the bottom-right Export menu (Ctrl+E). Hide meanings covers dictionary content; reveal the current meaning when needed, and the next lookup covers it again. The hiding preference is saved.

XT (XuTao)'s desktop tool for reading English PDFs, collecting vocabulary and making research notes. Read a page, leave a trace.

## Install and launch

Download XT-ReadTrace-1.14.0-Setup-x64.exe from [Releases](https://github.com/peekabooXT/XT-ReadTrace/releases), then run the installer. It includes the complete offline dictionary, English OCR data and runtime. Keep the desktop shortcut option enabled. No Python installation or account is required for the installed app.

The default installation folder is `D:\tools\codex\XT-ReadTrace`. Open the desktop shortcut named XT 阅迹, or run `XT阅迹.exe`. Keep the `_internal` and `dictionary` folders alongside the executable.

## Interface language

English is the default. Open Settings, select Interface language, and save. The interface switches immediately and remembers your choice for future launches. Available languages: Chinese, English, German, Japanese, French, Korean, Italian, Hindi, Spanish, Modern Standard Arabic, Portuguese and Russian. Arabic uses a right-to-left interface.

Language selection applies to reading tools, settings, dialogs, export options, help, status messages and errors. It does not translate the original PDF, collected English terms or your personal definitions. The bundled dictionary provides English–Chinese meanings. All language resources and open-license Noto fonts for Japanese, Korean, Arabic and Hindi are included for offline use.

## Read, collect and annotate

1. Import one or more English PDFs, or drag them into the window. Text PDFs and scanned PDFs are supported.
2. Double-click a word to collect it; double-click its colored bold underline again to remove that occurrence. Click or drag to select a phrase, check the text below, then press Enter to collect it.
3. Scroll continuously across pages. Choose continuous single pages or a two-page view, adjust zoom, jump to a page, or search the PDF.
4. Use Highlight text, Underline text, Freehand pen, Rectangle or Text note for reading annotations. Notes appear directly on the page, support multiple lines, and can be edited by double-clicking in Select / Read mode. Use the eraser, annotation manager, undo or redo to revise annotations.
5. The seven tool shortcuts default to 1–7 and can be changed in Settings. Shortcuts do not switch tools while you type in an editable field.

For a scan, run OCR on the current page first. The app uses bundled English OCR data. Check recognition results, especially in complex columns, tables, formulas or low-quality scans.

## Offline dictionary and personal meanings

The included ECDICT dictionary contains 770,611 entries. Select a word or type a query to see its meaning, pronunciation and possible base forms. If a phrase is missing, the app labels its component-word definitions clearly.

Use Edit / Add meaning to save your own explanation and optional pronunciation. Personal meanings are shared across PDFs, survive restarts and take priority in lookups and vocabulary-table exports. The bundled dictionary stays read-only. Restoring a dictionary meaning requires confirmation.

## Export one PDF or merge several wordbooks

- Wordbook TXT: export UTF-8 text compatible with MAiMemo's cloud wordbook. Chapter mode keeps one complete word or phrase per line and preserves case. Page chapters, plain text and the `//` base-form mode are also available. Base-form processing is performed by MAiMemo.
- Multiple PDFs: click Merge wordbooks in the Export menu, check the files, and preview the result. Select all or clear the selection as needed. Remove duplicates across files, optionally convert to lowercase, and export a single TXT wordbook. TXT can group entries by file, by file and page, or into one chapter.
- Printable vocabulary table: export an A4 PDF with English words or phrases on the left and meanings on the right. Preview and edit meanings for this export. Long meanings continue onto subsequent pages with repeated column headers. A merged table can include all checked PDFs and uses your saved personal meanings.
- Words and annotations PDF: create a copy containing collected-word styling and standard PDF annotations. Text notes remain directly visible and printable. The original PDF is preserved.
- Reading PDF with writing space: add one or two blank lines between visual text rows for handwritten notes. Choose all pages, the current page or a page range. Output uses A4 pagination and can include collected-word styling. Processing runs in the background and can be cancelled.

Merging reads the selected records without changing their PDFs, marks, notes or your reading position. The wordbook contains collected terms; reading highlights and other annotations are exported separately in the annotated PDF.

## Personal data and upgrades

The app stores your PDFs, vocabulary, notes, preferences and personal meanings in its local `data` folder. Exported files are normally saved in `exports`. Close the app and back up both folders when moving to another computer.

Installer upgrades preserve existing personal data. Uninstalling removes program files and shortcuts while leaving personal data. Source releases and initial installers exclude personal PDFs, library records, passwords and export files. PDF opening passwords are held in memory and are not saved to disk.

## Run from source

Use standalone CPython 3.12 or newer. An isolated environment is recommended to avoid Qt DLL conflicts with Anaconda. Installing Python dependencies may require internet access; the dictionary is bundled and can be prepared offline.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\src\requirements.txt
.\src\prepare_dictionary.ps1 -Python .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe .\src\app.py
```

`dictionary/ecdict.sqlite.gz` contains the full dictionary. The preparation script verifies checksums and decompresses it locally. Windows installers include the unpacked database. Dictionary source and checksum information are in `dictionary/source.json`; its MIT license is in `dictionary/LICENSE.txt`.

## Build and verify

```powershell
.\src\build.ps1 -Python python
.\tests\run_checks.ps1 -Python .\.venv\Scripts\python.exe
.\installer\build-installer.ps1 -ISCC 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' -Payload 'path-to-complete-payload'
```

Build with Inno Setup 6.7 or newer. Tests use generated samples and isolated temporary libraries. They cover reading, selection, continuous pages, OCR, dictionaries, annotations, exports, multi-file merging and language preferences. Installer payloads include language catalogs and exclude `data`, `exports`, `.git` and test artifacts.

## Author statement and license

Author: XT (XuTao). This project was developed with assistance from large language models and is fully open source under GNU AGPLv3; see [LICENSE](LICENSE). Third-party components retain their own licenses; see [Third-party notices](第三方说明.txt).

Without the author's authorization, the author does not provide commercial deployment, commercial customization or related support. This support policy does not restrict the rights granted by GNU AGPLv3 and does not prohibit commercial use permitted by that license. Commercial use must still comply with all applicable component licenses.

Suggestions and contact: [peekaboocatx@gmail.com](mailto:peekaboocatx@gmail.com).

## Acknowledgments

Thank you to [Hunan University of Science and Technology](https://www.hnust.edu.cn/), its [School of Computer Science and Engineering](https://computer.hnust.edu.cn/), and the Hunan Provincial Key Laboratory of Service Computing and Novel Software Service Technologies for providing an environment for study and research.

## Scope and translations

This app is independently developed and is not an official MAiMemo product. It does not log in to MAiMemo or upload wordbooks automatically. Offline lookup is not full-sentence machine translation. OCR, uncommon vocabulary and complex PDF layouts may require checking.

Translated interface text and READMEs were prepared with automated assistance; corrections are welcome at the contact address above. The English README is the documentation baseline. Code identifiers, stable file names and stored record keys use consistent project naming; see [Naming conventions](NAMING.md).

1.13.1: Freehand pen: hold Ctrl for a straight line or Shift for a wavy line. Hold the left mouse button and drag to erase annotations. Double-click collected words in Select / Read mode to remove their marks.

1.13.2: Reading PDF export continues across source pages to fill spare paper, while keeping blank pages, orientation changes and protected diagrams separate. Footer labels identify all source pages on each printed sheet.
