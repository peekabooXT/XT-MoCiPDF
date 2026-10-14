# XT 阅迹 · XT-ReadTrace

[English](README.md) | [简体中文](README.zh-CN.md) | [Deutsch](README.de.md) | [日本語](README.ja.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [Italiano](README.it.md) | [हिन्दी](README.hi.md) | [Español](README.es.md) | [العربية الفصحى](README.ar.md) | [Português](README.pt.md) | [Русский](README.ru.md)

L'outil de bureau de XT (XuTao) pour lire des PDF en anglais, collecter du vocabulaire et prendre des notes de recherche. Lire une page, laisser une trace.

## Installer et lancer

Téléchargez XT-ReadTrace-1.13.1-Setup-x64.exe depuis [Releases](https://github.com/peekabooXT/XT-ReadTrace/releases), puis exécutez le programme d'installation. Il comprend le dictionnaire hors ligne complet, les données OCR en anglais et le runtime. Gardez l'option de raccourci sur le bureau activée. Aucune installation ou compte Python n'est requis pour l'application installée.

Le dossier d'installation par défaut est `D:\tools\codex\XT-ReadTrace`. Ouvrez le raccourci sur le bureau nommé XT 阅迹 ou exécutez `XT阅迹.exe`. Conservez les dossiers `_internal` et `dictionary` à côté de l'exécutable.

## Langue de l'interface

L'anglais est la langue par défaut. Ouvrez Paramètres, sélectionnez la langue de l'interface et enregistrez. L'interface bascule immédiatement et mémorise votre choix pour les prochains lancements. Langues disponibles : chinois, anglais, allemand, japonais, français, coréen, italien, hindi, espagnol, arabe standard moderne, portugais et russe. L'arabe utilise une interface de droite à gauche.

La sélection de la langue s'applique aux outils de lecture, aux paramètres, aux boîtes de dialogue, aux options d'exportation, à l'aide, aux messages d'état et aux erreurs. Il ne traduit pas le PDF original, les termes anglais collectés ou vos définitions personnelles. Le dictionnaire fourni fournit des significations anglais-chinois. Toutes les ressources linguistiques et les polices Noto sous licence ouverte pour le japonais, le coréen, l'arabe et l'hindi sont incluses pour une utilisation hors ligne.

## Lire, collecter et annoter

1. Importez un ou plusieurs PDF anglais ou faites-les glisser dans la fenêtre. Les PDF texte et les PDF numérisés sont pris en charge.
2. Double-cliquez sur un mot pour le récupérer ; double-cliquez à nouveau sur son soulignement gras coloré pour supprimer cette occurrence. Cliquez ou faites glisser pour sélectionner une phrase, vérifiez le texte ci-dessous, puis appuyez sur Entrée pour la récupérer.
3. Faites défiler les pages en continu. Choisissez des pages simples continues ou une vue sur deux pages, ajustez le zoom, passez à une page ou effectuez une recherche dans le PDF.
4. Utilisez le texte surligné, le texte souligné, le stylo à main levée, le rectangle ou la note textuelle pour lire les annotations. Les notes apparaissent directement sur la page, prennent en charge plusieurs lignes et peuvent être modifiées en double-cliquant en mode Sélection/Lecture. Utilisez la gomme, le gestionnaire d'annotations, annulez ou refaites pour réviser les annotations.
5. Les sept raccourcis d'outils sont par défaut 1 à 7 et peuvent être modifiés dans Paramètres. Les raccourcis ne changent pas d'outil pendant que vous tapez dans un champ modifiable.

Pour une analyse, exécutez d'abord l'OCR sur la page actuelle. L'application utilise des données OCR anglaises groupées. Vérifiez les résultats de la reconnaissance, en particulier dans les colonnes, tableaux, formules complexes ou analyses de mauvaise qualité.

## Dictionnaire hors ligne et significations personnelles

Le dictionnaire ECDICT inclus contient 770 611 entrées. Sélectionnez un mot ou tapez une requête pour voir sa signification, sa prononciation et ses formes de base possibles. Si une phrase est manquante, l'application étiquette clairement ses définitions de mots composants.

Utilisez Modifier/Ajouter une signification pour enregistrer votre propre explication et votre prononciation facultative. Les significations personnelles sont partagées dans les PDF, survivent aux redémarrages et sont prioritaires dans les recherches et les exportations de tables de vocabulaire. Le dictionnaire fourni reste en lecture seule. La restauration du sens d'un dictionnaire nécessite une confirmation.

## Exportez un PDF ou fusionnez plusieurs manuels de mots

- Wordbook TXT : exportez du texte UTF-8 compatible avec le wordbook cloud de MAiMemo. Le mode chapitre conserve un mot ou une phrase complète par ligne et préserve la casse. Des chapitres de page, du texte brut et le mode de formulaire de base `//` sont également disponibles. Le traitement du formulaire de base est effectué par MAiMemo.
- Plusieurs PDF : cliquez sur Fusionner les manuels de mots sous la liste des documents, vérifiez les fichiers et prévisualisez le résultat. Sélectionnez tout ou effacez la sélection selon vos besoins. Supprimez les doublons dans les fichiers, convertissez éventuellement en minuscules et exportez un seul manuel de mots TXT. TXT peut regrouper les entrées par fichier, par fichier et page, ou en un seul chapitre.
- Tableau de vocabulaire imprimable : exportez un PDF A4 avec des mots ou des phrases en anglais à gauche et leurs significations à droite. Prévisualisez et modifiez les significations de cette exportation. Les significations longues se poursuivent sur les pages suivantes avec des en-têtes de colonnes répétés. Un tableau fusionné peut inclure tous les PDF vérifiés et utilise vos significations personnelles enregistrées.
- Mots et annotations PDF : créez une copie contenant le style des mots collectés et les annotations PDF standard. Les notes textuelles restent directement visibles et imprimables. Le PDF original est conservé.
- Lecture de PDF avec espace d'écriture : ajoutez une ou deux lignes vierges entre les lignes de texte visuel pour les notes manuscrites. Choisissez toutes les pages, la page actuelle ou une plage de pages. La sortie utilise une pagination A4 et peut inclure un style de mots collectés. Le traitement s'exécute en arrière-plan et peut être annulé.

La fusion lit les enregistrements sélectionnés sans modifier leurs PDF, leurs marques, leurs notes ou votre position de lecture. Le manuel de mots contient des termes collectés ; Les surbrillances de lecture et autres annotations sont exportées séparément dans le PDF annoté.

## Données personnelles et mises à niveau

L'application stocke vos PDF, vocabulaire, notes, préférences et significations personnelles dans son dossier `data` local. Les fichiers exportés sont normalement enregistrés dans `exports`. Fermez l'application et sauvegardez les deux dossiers lorsque vous passez à un autre ordinateur.

Les mises à niveau du programme d'installation préservent les données personnelles existantes. La désinstallation supprime les fichiers du programme et les raccourcis tout en laissant les données personnelles. Les versions sources et les installateurs initiaux excluent les fichiers PDF personnels, les enregistrements de bibliothèque, les mots de passe et les fichiers d'exportation. Les mots de passe d'ouverture des PDF sont conservés en mémoire et ne sont pas enregistrés sur le disque.

## Exécuter à partir des sources

Utilisez CPython 3.12 autonome ou une version plus récente. Un environnement isolé est recommandé pour éviter les conflits de DLL Qt avec Anaconda. L'installation des dépendances Python peut nécessiter un accès à Internet ; le dictionnaire est fourni et peut être préparé hors ligne.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\src\requirements.txt
.\src\prepare_dictionary.ps1 -Python .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe .\src\app.py
```

`dictionary/ecdict.sqlite.gz` contient le dictionnaire complet. Le script de préparation vérifie les sommes de contrôle et les décompresse localement. Les installateurs Windows incluent la base de données décompressée. La source du dictionnaire et les informations sur la somme de contrôle sont au format `dictionary/source.json` ; sa licence MIT est en `dictionary/LICENSE.txt`.

## Construire et vérifier

```powershell
.\src\build.ps1 -Python python
.\tests\run_checks.ps1 -Python .\.venv\Scripts\python.exe
.\installer\build-installer.ps1 -ISCC 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' -Payload 'path-to-complete-payload'
```

Construisez avec Inno Setup 6.7 ou plus récent. Les tests utilisent des échantillons générés et des bibliothèques temporaires isolées. Ils couvrent la lecture, la sélection, les pages continues, l'OCR, les dictionnaires, les annotations, les exportations, la fusion multi-fichiers et les préférences linguistiques. Les charges utiles du programme d'installation incluent les catalogues de langues et excluent `data`, `exports`, `.git` et les artefacts de test.

## Déclaration de l'auteur et licence

Auteur : XT (XuTao). Ce projet a été développé avec l'aide de grands modèles de langage et est entièrement open source sous GNU AGPLv3 ; voir [LICENSE](LICENSE). Les composants tiers conservent leurs propres licences ; voir [Third-party notices](第三方说明.txt).

Sans l'autorisation de l'auteur, l'auteur ne fournit pas de déploiement commercial, de personnalisation commerciale ou de support connexe. Cette politique de support ne restreint pas les droits accordés par GNU AGPLv3 et n'interdit pas l'utilisation commerciale autorisée par cette licence. L'utilisation commerciale doit toujours être conforme à toutes les licences de composants applicables.

Suggestions et contact : [peekaboocatx@gmail.com](mailto:peekaboocatx@gmail.com).

## Remerciements

Merci à [Hunan University of Science and Technology](https://www.hnust.edu.cn/), à son [School of Computer Science and Engineering](https://computer.hnust.edu.cn/) et au laboratoire clé provincial du Hunan pour l'informatique de service et les nouvelles technologies de services logiciels pour avoir fourni un environnement d'étude et de recherche.

## Portée et traductions

Cette application est développée indépendamment et n'est pas un produit officiel MAiMemo. Il ne se connecte pas à MAiMemo et ne télécharge pas automatiquement les manuels de mots. La recherche hors ligne n’est pas une traduction automatique de phrases complètes. L'OCR, le vocabulaire peu courant et les mises en page PDF complexes peuvent nécessiter une vérification.

Le texte de l'interface traduit et les README ont été préparés avec une assistance automatisée ; les corrections sont les bienvenues à l’adresse de contact ci-dessus. Le fichier README en anglais constitue la base de la documentation. Les identifiants de code, les noms de fichiers stables et les clés d'enregistrement stockées utilisent une dénomination de projet cohérente ; voir [Naming conventions](NAMING.md).

1.13.1: Stylo libre : maintenez Ctrl pour une ligne droite ou Shift pour une ligne ondulée. Maintenez le bouton gauche et faites glisser pour effacer les annotations. Double-cliquez sur les mots collectés en mode lecture pour retirer leurs marques.
