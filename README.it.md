# XT 阅迹 · XT-ReadTrace

[English](README.md) | [简体中文](README.zh-CN.md) | [Deutsch](README.de.md) | [日本語](README.ja.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [Italiano](README.it.md) | [हिन्दी](README.hi.md) | [Español](README.es.md) | [العربية الفصحى](README.ar.md) | [Português](README.pt.md) | [Русский](README.ru.md)

Lo strumento desktop di XT (XuTao) per leggere PDF in inglese, raccogliere vocabolario e prendere appunti di ricerca. Leggi una pagina, lascia una traccia.

## Installa e avvia

Scarica XT-ReadTrace-1.13.2-Setup-x64.exe da [Releases](https://github.com/peekabooXT/XT-ReadTrace/releases), quindi esegui il programma di installazione. Include il dizionario offline completo, i dati OCR inglesi e il runtime. Mantieni abilitata l'opzione di collegamento sul desktop. Non è richiesta alcuna installazione o account Python per l'app installata.

La cartella di installazione predefinita è `D:\tools\codex\XT-ReadTrace`. Apri il collegamento sul desktop denominato XT 阅迹 o esegui `XT阅迹.exe`. Conserva le cartelle `_internal` e `dictionary` insieme all'eseguibile.

## Linguaggio dell'interfaccia

L'inglese è l'impostazione predefinita. Apri Impostazioni, seleziona Lingua interfaccia e salva. L'interfaccia cambia immediatamente e ricorda la tua scelta per i lanci futuri. Lingue disponibili: cinese, inglese, tedesco, giapponese, francese, coreano, italiano, hindi, spagnolo, arabo standard moderno, portoghese e russo. L'arabo utilizza un'interfaccia da destra a sinistra.

La selezione della lingua si applica a strumenti di lettura, impostazioni, finestre di dialogo, opzioni di esportazione, guida, messaggi di stato ed errori. Non traduce il PDF originale, i termini inglesi raccolti o le tue definizioni personali. Il dizionario in bundle fornisce significati inglese-cinese. Tutte le risorse linguistiche e i caratteri Noto con licenza aperta per giapponese, coreano, arabo e hindi sono inclusi per l'utilizzo offline.

## Leggi, raccogli e annota

1. Importa uno o più PDF in inglese o trascinali nella finestra. Sono supportati PDF di testo e PDF scansionati.
2. Fare doppio clic su una parola per raccoglierla; fare nuovamente doppio clic sulla sottolineatura in grassetto colorata per rimuovere tale occorrenza. Fai clic o trascina per selezionare una frase, controlla il testo sottostante, quindi premi Invio per raccoglierla.
3. Scorri continuamente tra le pagine. Scegli pagine singole continue o una visualizzazione di due pagine, regola lo zoom, passa a una pagina o cerca nel PDF.
4. Utilizzare Evidenzia testo, Sottolinea testo, Penna a mano libera, Rettangolo o Nota di testo per leggere le annotazioni. Le note vengono visualizzate direttamente sulla pagina, supportano più righe e possono essere modificate facendo doppio clic in modalità Seleziona/Leggi. Utilizza la gomma, il gestore delle annotazioni, annulla o ripristina per rivedere le annotazioni.
5. Le sette scorciatoie degli strumenti sono predefinite da 1 a 7 e possono essere modificate in Impostazioni. Le scorciatoie non cambiano strumento mentre digiti in un campo modificabile.

Per una scansione, esegui prima l'OCR sulla pagina corrente. L'app utilizza dati OCR inglesi in bundle. Controlla i risultati del riconoscimento, soprattutto in colonne, tabelle, formule complesse o scansioni di bassa qualità.

## Dizionario offline e significati personali

Il dizionario ECDICT incluso contiene 770.611 voci. Seleziona una parola o digita una query per vederne il significato, la pronuncia e le possibili forme base. Se manca una frase, l'app etichetta chiaramente le definizioni delle parole che la compongono.

Utilizza Modifica/Aggiungi significato per salvare la tua spiegazione e la pronuncia opzionale. I significati personali sono condivisi tra i PDF, sopravvivono ai riavvii e hanno la priorità nelle ricerche e nelle esportazioni delle tabelle di vocabolario. Il dizionario in bundle rimane di sola lettura. Il ripristino del significato di un dizionario richiede conferma.

## Esporta un PDF o unisci diversi libri di parole

- Wordbook TXT: esporta testo UTF-8 compatibile con il wordbook cloud di MAiMemo. La modalità capitolo mantiene una parola o una frase completa per riga e preserva le maiuscole e minuscole. Sono inoltre disponibili i capitoli di pagina, il testo semplice e la modalità formato base `//`. L'elaborazione del modulo base viene eseguita da MAiMemo.
- Più PDF: fai clic su Unisci libri di parole sotto l'elenco dei documenti, controlla i file e visualizza l'anteprima del risultato. Seleziona tutto o deseleziona la selezione secondo necessità. Rimuovi i duplicati tra i file, facoltativamente converti in minuscolo ed esporta un singolo wordbook TXT. TXT può raggruppare le voci per file, per file e pagina o in un capitolo.
- Tabella dei vocaboli stampabile: esporta un PDF A4 con parole o frasi inglesi a sinistra e significati a destra. Visualizza in anteprima e modifica i significati per questa esportazione. I significati lunghi continuano nelle pagine successive con intestazioni di colonna ripetute. Una tabella unita può includere tutti i PDF selezionati e utilizza i significati personali salvati.
- PDF con parole e annotazioni: crea una copia contenente lo stile delle parole raccolte e le annotazioni PDF standard. Le note di testo rimangono direttamente visibili e stampabili. Il PDF originale viene conservato.
- Lettura di PDF con spazio di scrittura: aggiungi una o due righe vuote tra le righe di testo visivo per le note scritte a mano. Scegli tutte le pagine, la pagina corrente o un intervallo di pagine. L'output utilizza l'impaginazione A4 e può includere lo stile delle parole raccolte. L'elaborazione viene eseguita in background e può essere annullata.

L'unione legge i record selezionati senza modificare i relativi PDF, segni, note o la posizione di lettura. Il wordbook contiene termini raccolti; i punti salienti della lettura e altre annotazioni vengono esportati separatamente nel PDF con annotazioni.

## Dati personali e aggiornamenti

L'app memorizza i tuoi PDF, vocabolario, note, preferenze e significati personali nella cartella `data` locale. I file esportati vengono normalmente salvati in `exports`. Chiudi l'app ed esegui il backup di entrambe le cartelle quando passi a un altro computer.

Gli aggiornamenti dell'installatore conservano i dati personali esistenti. La disinstallazione rimuove i file di programma e i collegamenti lasciando i dati personali. Le versioni sorgente e i programmi di installazione iniziali escludono PDF personali, record di libreria, password e file di esportazione. Le password di apertura dei PDF vengono conservate in memoria e non vengono salvate su disco.

## Esegui dalla fonte

Utilizzare CPython 3.12 autonomo o versione successiva. Si consiglia un ambiente isolato per evitare conflitti tra DLL Qt e Anaconda. L'installazione delle dipendenze Python potrebbe richiedere l'accesso a Internet; il dizionario è in bundle e può essere preparato offline.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\src\requirements.txt
.\src\prepare_dictionary.ps1 -Python .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe .\src\app.py
```

`dictionary/ecdict.sqlite.gz` contiene il dizionario completo. Lo script di preparazione verifica i checksum e li decomprime localmente. I programmi di installazione di Windows includono il database decompresso. La fonte del dizionario e le informazioni sul checksum si trovano in `dictionary/source.json`; la sua licenza MIT è in `dictionary/LICENSE.txt`.

## Costruisci e verifica

```powershell
.\src\build.ps1 -Python python
.\tests\run_checks.ps1 -Python .\.venv\Scripts\python.exe
.\installer\build-installer.ps1 -ISCC 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' -Payload 'path-to-complete-payload'
```

Costruisci con Inno Setup 6.7 o versione successiva. I test utilizzano campioni generati e librerie temporanee isolate. Riguardano la lettura, la selezione, le pagine continue, l'OCR, i dizionari, le annotazioni, le esportazioni, l'unione di più file e le preferenze della lingua. I payload dell'installatore includono cataloghi linguistici ed escludono `data`, `exports`, `.git` e artefatti di test.

## Dichiarazione e licenza dell'autore

Autore: XT (XuTao). Questo progetto è stato sviluppato con l'assistenza di grandi modelli linguistici ed è completamente open source sotto GNU AGPLv3; vedere [LICENSE](LICENSE). I componenti di terze parti mantengono le proprie licenze; vedere [Third-party notices](第三方说明.txt).

Senza l'autorizzazione dell'autore, l'autore non fornisce distribuzione commerciale, personalizzazione commerciale o supporto correlato. Questa politica di supporto non limita i diritti concessi da GNU AGPLv3 e non vieta l'uso commerciale consentito da tale licenza. L'uso commerciale deve comunque rispettare tutte le licenze dei componenti applicabili.

Suggerimenti e contatti: [peekaboocatx@gmail.com](mailto:peekaboocatx@gmail.com).

## Ringraziamenti

Grazie a [Hunan University of Science and Technology](https://www.hnust.edu.cn/), al suo [School of Computer Science and Engineering](https://computer.hnust.edu.cn/) e al Laboratorio chiave provinciale di Hunan per l'elaborazione dei servizi e le nuove tecnologie di servizi software per aver fornito un ambiente per lo studio e la ricerca.

## Ambito e traduzioni

Questa app è sviluppata in modo indipendente e non è un prodotto MAiMemo ufficiale. Non accede a MAiMemo né carica automaticamente i libri di parole. La ricerca offline non è una traduzione automatica dell'intera frase. OCR, vocabolario non comune e layout PDF complessi potrebbero richiedere un controllo.

Il testo dell'interfaccia tradotto e i README sono stati preparati con l'assistenza automatizzata; le correzioni sono benvenute all'indirizzo di contatto sopra. Il README inglese è la base della documentazione. Gli identificatori di codice, i nomi di file stabili e le chiavi di record archiviate utilizzano nomi di progetto coerenti; vedere [Naming conventions](NAMING.md).

1.13.1: Penna libera: tieni premuto Ctrl per una linea retta o Shift per una linea ondulata. Tieni premuto il pulsante sinistro e trascina per cancellare le annotazioni. Fai doppio clic sulle parole raccolte in modalità lettura per rimuovere i segni.
