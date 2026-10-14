# XT 阅迹 · XT-ReadTrace

[English](README.md) | [简体中文](README.zh-CN.md) | [Deutsch](README.de.md) | [日本語](README.ja.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [Italiano](README.it.md) | [हिन्दी](README.hi.md) | [Español](README.es.md) | [العربية الفصحى](README.ar.md) | [Português](README.pt.md) | [Русский](README.ru.md)

Das Desktop-Tool von XT (XuTao) zum Lesen englischer PDFs, zum Sammeln von Vokabeln und zum Erstellen von Forschungsnotizen. Eine Seite lesen, eine Spur hinterlassen.

## Installieren und starten

Laden Sie XT-ReadTrace-1.13.0-Setup-x64.exe von [Releases](https://github.com/peekabooXT/XT-ReadTrace/releases) herunter und führen Sie dann das Installationsprogramm aus. Es umfasst das komplette Offline-Wörterbuch, englische OCR-Daten und Laufzeit. Lassen Sie die Desktop-Verknüpfungsoption aktiviert. Für die installierte App ist keine Python-Installation oder ein Python-Konto erforderlich.

Der Standardinstallationsordner ist `D:\tools\codex\XT-ReadTrace`. Öffnen Sie die Desktop-Verknüpfung mit dem Namen XT 阅迹 oder führen Sie `XT阅迹.exe` aus. Behalten Sie die Ordner `_internal` und `dictionary` neben der ausführbaren Datei.

## Schnittstellensprache

Englisch ist die Standardeinstellung. Öffnen Sie die Einstellungen, wählen Sie die Sprache der Benutzeroberfläche aus und speichern Sie. Die Benutzeroberfläche wechselt sofort und merkt sich Ihre Auswahl für zukünftige Starts. Verfügbare Sprachen: Chinesisch, Englisch, Deutsch, Japanisch, Französisch, Koreanisch, Italienisch, Hindi, Spanisch, modernes Hocharabisch, Portugiesisch und Russisch. Arabisch verwendet eine Rechts-nach-Links-Schnittstelle.

Die Sprachauswahl gilt für Lesetools, Einstellungen, Dialoge, Exportoptionen, Hilfe, Statusmeldungen und Fehler. Das Original-PDF, gesammelte englische Begriffe oder Ihre persönlichen Definitionen werden nicht übersetzt. Das mitgelieferte Wörterbuch bietet englisch-chinesische Bedeutungen. Alle Sprachressourcen und Noto-Schriftarten mit offener Lizenz für Japanisch, Koreanisch, Arabisch und Hindi sind für die Offline-Nutzung enthalten.

## Lesen, sammeln und kommentieren

1. Importieren Sie ein oder mehrere englische PDFs oder ziehen Sie sie in das Fenster. Text-PDFs und gescannte PDFs werden unterstützt.
2. Doppelklicken Sie auf ein Wort, um es zu sammeln. Doppelklicken Sie erneut auf die farbige Fettunterstreichung, um das Vorkommen zu entfernen. Klicken oder ziehen Sie, um eine Phrase auszuwählen, überprüfen Sie den Text unten und drücken Sie dann die Eingabetaste, um ihn zu erfassen.
3. Scrollen Sie kontinuierlich über die Seiten. Wählen Sie fortlaufende Einzelseiten oder eine Zweiseitenansicht, passen Sie den Zoom an, springen Sie zu einer Seite oder durchsuchen Sie das PDF.
4. Verwenden Sie Text hervorheben, Text unterstreichen, Freihandstift, Rechteck oder Textnotiz zum Lesen von Anmerkungen. Notizen erscheinen direkt auf der Seite, unterstützen mehrere Zeilen und können durch Doppelklick im Auswahl-/Lesemodus bearbeitet werden. Verwenden Sie den Radierer, den Anmerkungsmanager sowie „Rückgängig“ oder „Wiederherstellen“, um Anmerkungen zu überarbeiten.
5. Die sieben Werkzeugverknüpfungen sind standardmäßig auf 1–7 eingestellt und können in den Einstellungen geändert werden. Tastenkombinationen wechseln nicht zwischen Werkzeugen, während Sie in ein bearbeitbares Feld tippen.

Führen Sie für einen Scan zunächst OCR auf der aktuellen Seite aus. Die App verwendet gebündelte englische OCR-Daten. Überprüfen Sie die Erkennungsergebnisse, insbesondere in komplexen Spalten, Tabellen, Formeln oder Scans mit geringer Qualität.

## Offline-Wörterbuch und persönliche Bedeutungen

Das mitgelieferte ECDICT-Wörterbuch enthält 770.611 Einträge. Wählen Sie ein Wort aus oder geben Sie eine Abfrage ein, um dessen Bedeutung, Aussprache und mögliche Grundformen anzuzeigen. Wenn eine Phrase fehlt, beschriftet die App die zugehörigen Wortdefinitionen deutlich.

Verwenden Sie „Bearbeiten/Bedeutung hinzufügen“, um Ihre eigene Erklärung und optionale Aussprache zu speichern. Persönliche Bedeutungen werden in allen PDFs geteilt, überleben Neustarts und haben bei Suchvorgängen und Vokabeltabellen-Exporten Vorrang. Das mitgelieferte Wörterbuch bleibt schreibgeschützt. Das Wiederherstellen einer Wörterbuchbedeutung erfordert eine Bestätigung.

## Exportieren Sie ein PDF oder führen Sie mehrere Wortbücher zusammen

- Wordbook TXT: Exportieren Sie UTF-8-Text, der mit dem Cloud-Wortbuch von MAiMemo kompatibel ist. Der Kapitelmodus behält ein vollständiges Wort oder einen vollständigen Satz pro Zeile bei und behält die Groß-/Kleinschreibung bei. Seitenkapitel, einfacher Text und der `//`-Basisformularmodus sind ebenfalls verfügbar. Die Basisformularverarbeitung wird von MAiMemo durchgeführt.
- Mehrere PDFs: Klicken Sie unterhalb der Dokumentliste auf „Wortbücher zusammenführen“, überprüfen Sie die Dateien und zeigen Sie eine Vorschau des Ergebnisses an. Wählen Sie alle aus oder löschen Sie die Auswahl nach Bedarf. Entfernen Sie Duplikate aus allen Dateien, konvertieren Sie sie optional in Kleinbuchstaben und exportieren Sie ein einzelnes TXT-Wortbuch. TXT kann Einträge nach Datei, nach Datei und Seite oder in einem Kapitel gruppieren.
- Druckbare Vokabeltabelle: Exportieren Sie ein A4-PDF mit englischen Wörtern oder Phrasen auf der linken Seite und Bedeutungen auf der rechten Seite. Sehen Sie sich die Bedeutungen für diesen Export in der Vorschau an und bearbeiten Sie sie. Lange Bedeutungen werden auf den Folgeseiten mit wiederholten Spaltenüberschriften fortgesetzt. Eine zusammengeführte Tabelle kann alle überprüften PDFs enthalten und verwendet Ihre gespeicherten persönlichen Bedeutungen.
- PDF mit Wörtern und Anmerkungen: Erstellen Sie eine Kopie mit gesammelten Wortstilen und Standard-PDF-Anmerkungen. Textnotizen bleiben direkt sichtbar und ausdruckbar. Das Original-PDF bleibt erhalten.
- Lesen von PDFs mit Platz zum Schreiben: Fügen Sie eine oder zwei Leerzeilen zwischen visuellen Textzeilen für handschriftliche Notizen ein. Wählen Sie alle Seiten, die aktuelle Seite oder einen Seitenbereich. Die Ausgabe verwendet eine A4-Paginierung und kann den Stil gesammelter Wörter enthalten. Die Verarbeitung läuft im Hintergrund und kann abgebrochen werden.

Beim Zusammenführen werden die ausgewählten Datensätze gelesen, ohne deren PDFs, Markierungen, Notizen oder Ihre Leseposition zu ändern. Das Wortbuch enthält gesammelte Begriffe; Lesehervorhebungen und andere Anmerkungen werden separat in das mit Anmerkungen versehene PDF exportiert.

## Persönliche Daten und Upgrades

Die App speichert Ihre PDFs, Vokabeln, Notizen, Vorlieben und persönlichen Bedeutungen in ihrem lokalen `data`-Ordner. Exportierte Dateien werden normalerweise in `exports` gespeichert. Schließen Sie die App und sichern Sie beide Ordner, wenn Sie auf einen anderen Computer wechseln.

Bei Installer-Upgrades bleiben vorhandene personenbezogene Daten erhalten. Durch die Deinstallation werden Programmdateien und Verknüpfungen entfernt, persönliche Daten bleiben jedoch erhalten. Quellversionen und Erstinstallationsprogramme schließen persönliche PDFs, Bibliothekseinträge, Passwörter und Exportdateien aus. Passwörter zum Öffnen von PDF-Dateien werden im Speicher gespeichert und nicht auf der Festplatte gespeichert.

## Von der Quelle ausführen

Verwenden Sie eigenständiges CPython 3.12 oder neuer. Um Qt-DLL-Konflikte mit Anaconda zu vermeiden, wird eine isolierte Umgebung empfohlen. Für die Installation von Python-Abhängigkeiten ist möglicherweise ein Internetzugang erforderlich. Das Wörterbuch ist gebündelt und kann offline erstellt werden.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\src\requirements.txt
.\src\prepare_dictionary.ps1 -Python .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe .\src\app.py
```

`dictionary/ecdict.sqlite.gz` enthält das vollständige Wörterbuch. Das Vorbereitungsskript überprüft Prüfsummen und dekomprimiert sie lokal. Windows-Installationsprogramme enthalten die entpackte Datenbank. Wörterbuchquellen- und Prüfsummeninformationen befinden sich in `dictionary/source.json`; seine MIT-Lizenz ist in `dictionary/LICENSE.txt`.

## Erstellen und überprüfen

```powershell
.\src\build.ps1 -Python python
.\tests\run_checks.ps1 -Python .\.venv\Scripts\python.exe
.\installer\build-installer.ps1 -ISCC 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' -Payload 'path-to-complete-payload'
```

Erstellen Sie mit Inno Setup 6.7 oder neuer. Tests verwenden generierte Beispiele und isolierte temporäre Bibliotheken. Sie umfassen Lesen, Auswahl, fortlaufende Seiten, OCR, Wörterbücher, Anmerkungen, Exporte, Zusammenführen mehrerer Dateien und Spracheinstellungen. Die Nutzdaten des Installationsprogramms umfassen Sprachkataloge und schließen `data`, `exports`, `.git` und Testartefakte aus.

## Autorenerklärung und Lizenz

Autor: XT (XuTao). Dieses Projekt wurde mit Unterstützung großer Sprachmodelle entwickelt und ist vollständig Open Source unter GNU AGPLv3; siehe [LICENSE](LICENSE). Komponenten von Drittanbietern behalten ihre eigenen Lizenzen; siehe [Third-party notices](第三方说明.txt).

Ohne die Genehmigung des Autors bietet der Autor keine kommerzielle Bereitstellung, kommerzielle Anpassung oder damit verbundenen Support an. Diese Supportrichtlinie schränkt die durch GNU AGPLv3 gewährten Rechte nicht ein und verbietet nicht die durch diese Lizenz gestattete kommerzielle Nutzung. Bei der kommerziellen Nutzung müssen weiterhin alle geltenden Komponentenlizenzen eingehalten werden.

Vorschläge und Kontakt: [peekaboocatx@gmail.com](mailto:peekaboocatx@gmail.com).

## Danksagungen

Vielen Dank an [Hunan University of Science and Technology](https://www.hnust.edu.cn/), sein [School of Computer Science and Engineering](https://computer.hnust.edu.cn/) und das Hunan Provincial Key Laboratory of Service Computing and Novel Software Service Technologies für die Bereitstellung einer Umgebung für Studium und Forschung.

## Umfang und Übersetzungen

Diese App wurde unabhängig entwickelt und ist kein offizielles MAiMemo-Produkt. Es erfolgt keine Anmeldung bei MAiMemo oder das automatische Hochladen von Wortbüchern. Bei der Offline-Suche handelt es sich nicht um eine vollständige maschinelle Übersetzung. OCR, ungewöhnlicher Wortschatz und komplexe PDF-Layouts erfordern möglicherweise eine Überprüfung.

Übersetzte Schnittstellentexte und READMEs wurden mit automatisierter Unterstützung erstellt; Korrekturen sind unter der oben genannten Kontaktadresse willkommen. Die englische README-Datei ist die Basisdokumentation. Code-IDs, stabile Dateinamen und gespeicherte Datensatzschlüssel verwenden eine konsistente Projektbenennung; siehe [Naming conventions](NAMING.md).
