# XT 阅迹 · XT-ReadTrace

[English](README.md) | [简体中文](README.zh-CN.md) | [Deutsch](README.de.md) | [日本語](README.ja.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [Italiano](README.it.md) | [हिन्दी](README.hi.md) | [Español](README.es.md) | [العربية الفصحى](README.ar.md) | [Português](README.pt.md) | [Русский](README.ru.md)

La herramienta de escritorio de XT (XuTao) para leer archivos PDF en inglés, recopilar vocabulario y tomar notas de investigación. Lee una página, deja un rastro.

## Instalar y ejecutar

Descargue XT-ReadTrace-1.13.0-Setup-x64.exe desde [Releases](https://github.com/peekabooXT/XT-ReadTrace/releases) y luego ejecute el instalador. Incluye el diccionario completo sin conexión, datos OCR en inglés y tiempo de ejecución. Mantenga habilitada la opción de acceso directo del escritorio. No se requiere ninguna instalación o cuenta de Python para la aplicación instalada.

La carpeta de instalación predeterminada es `D:\tools\codex\XT-ReadTrace`. Abra el acceso directo del escritorio llamado XT 阅迹 o ejecute `XT阅迹.exe`. Mantenga las carpetas `_internal` y `dictionary` junto al ejecutable.

## Idioma de la interfaz

El inglés es el predeterminado. Abra Configuración, seleccione Idioma de la interfaz y guarde. La interfaz cambia inmediatamente y recuerda su elección para futuros lanzamientos. Idiomas disponibles: chino, inglés, alemán, japonés, francés, coreano, italiano, hindi, español, árabe estándar moderno, portugués y ruso. El árabe utiliza una interfaz de derecha a izquierda.

La selección de idioma se aplica a las herramientas de lectura, configuraciones, cuadros de diálogo, opciones de exportación, ayuda, mensajes de estado y errores. No traduce el PDF original, los términos recopilados en inglés ni sus definiciones personales. El diccionario incluido proporciona significados entre inglés y chino. Todos los recursos lingüísticos y las fuentes Noto de licencia abierta para japonés, coreano, árabe e hindi se incluyen para uso sin conexión.

## Leer, recopilar y anotar

1. Importe uno o más archivos PDF en inglés o arrástrelos a la ventana. Se admiten archivos PDF de texto y archivos PDF escaneados.
2. Haga doble clic en una palabra para recopilarla; haga doble clic en el subrayado en negrita de color nuevamente para eliminar esa ocurrencia. Haga clic o arrastre para seleccionar una frase, verifique el texto a continuación y luego presione Entrar para recopilarla.
3. Desplácese continuamente por las páginas. Elija páginas individuales continuas o una vista de dos páginas, ajuste el zoom, salte a una página o busque en el PDF.
4. Utilice Resaltar texto, Subrayar texto, Lápiz a mano alzada, Rectángulo o Nota de texto para leer anotaciones. Las notas aparecen directamente en la página, admiten varias líneas y se pueden editar haciendo doble clic en el modo Seleccionar/Leer. Utilice el borrador, el administrador de anotaciones, deshacer o rehacer para revisar las anotaciones.
5. Los siete atajos de herramientas están predeterminados del 1 al 7 y se pueden cambiar en Configuración. Los atajos no cambian de herramienta mientras escribe en un campo editable.

Para escanear, primero ejecute OCR en la página actual. La aplicación utiliza datos OCR en inglés incluidos. Verifique los resultados del reconocimiento, especialmente en columnas, tablas, fórmulas complejas o escaneos de baja calidad.

## Diccionario sin conexión y significados personales.

El diccionario ECDICT incluido contiene 770.611 entradas. Seleccione una palabra o escriba una consulta para ver su significado, pronunciación y posibles formas base. Si falta una frase, la aplicación etiqueta claramente las definiciones de las palabras que la componen.

Utilice Editar/Agregar significado para guardar su propia explicación y pronunciación opcional. Los significados personales se comparten entre archivos PDF, sobreviven a los reinicios y tienen prioridad en las búsquedas y exportaciones de tablas de vocabulario. El diccionario incluido permanece como de sólo lectura. Restaurar el significado de un diccionario requiere confirmación.

## Exporte un PDF o combine varios libros de palabras

- Wordbook TXT: exporta texto UTF-8 compatible con el libro de palabras en la nube de MAiMemo. El modo Capítulo mantiene una palabra o frase completa por línea y conserva las mayúsculas y minúsculas. También están disponibles los capítulos de página, texto sin formato y el modo de formulario base `//`. El procesamiento del formulario base lo realiza MAiMemo.
- Varios archivos PDF: haga clic en Combinar libros de palabras debajo de la lista de documentos, verifique los archivos y obtenga una vista previa del resultado. Seleccione todo o borre la selección según sea necesario. Elimine duplicados en archivos, opcionalmente convierta a minúsculas y exporte un único libro de palabras TXT. TXT puede agrupar entradas por archivo, por archivo y página, o en un capítulo.
- Tabla de vocabulario imprimible: exporte un PDF A4 con palabras o frases en inglés a la izquierda y significados a la derecha. Obtenga una vista previa y edite los significados de esta exportación. Los significados largos continúan en páginas siguientes con encabezados de columna repetidos. Una tabla combinada puede incluir todos los archivos PDF verificados y utiliza sus significados personales guardados.
- PDF de palabras y anotaciones: cree una copia que contenga estilos de palabras recopiladas y anotaciones de PDF estándar. Las notas de texto permanecen directamente visibles e imprimibles. Se conserva el PDF original.
- Lectura de PDF con espacio para escribir: agregue una o dos líneas en blanco entre las filas de texto visual para notas escritas a mano. Elija todas las páginas, la página actual o un rango de páginas. La salida utiliza paginación A4 y puede incluir estilos de palabras recopiladas. El procesamiento se ejecuta en segundo plano y se puede cancelar.

La combinación lee los registros seleccionados sin cambiar sus archivos PDF, marcas, notas o su posición de lectura. El libro de palabras contiene términos recopilados; Los aspectos destacados de la lectura y otras anotaciones se exportan por separado en el PDF anotado.

## Datos personales y actualizaciones

La aplicación almacena sus archivos PDF, vocabulario, notas, preferencias y significados personales en su carpeta local `data`. Los archivos exportados normalmente se guardan en `exports`. Cierre la aplicación y haga una copia de seguridad de ambas carpetas cuando se mude a otra computadora.

Las actualizaciones del instalador preservan los datos personales existentes. La desinstalación elimina archivos de programa y accesos directos y deja datos personales. Las versiones de origen y los instaladores iniciales excluyen archivos PDF personales, registros de biblioteca, contraseñas y archivos de exportación. Las contraseñas de apertura de PDF se guardan en la memoria y no se guardan en el disco.

## Ejecutar desde la fuente

Utilice CPython 3.12 independiente o posterior. Se recomienda un entorno aislado para evitar conflictos de DLL de Qt con Anaconda. La instalación de dependencias de Python puede requerir acceso a Internet; el diccionario está incluido y se puede preparar sin conexión.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\src\requirements.txt
.\src\prepare_dictionary.ps1 -Python .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe .\src\app.py
```

`dictionary/ecdict.sqlite.gz` contiene el diccionario completo. El script de preparación verifica las sumas de verificación y lo descomprime localmente. Los instaladores de Windows incluyen la base de datos descomprimida. La fuente del diccionario y la información de la suma de comprobación se encuentran en `dictionary/source.json`; su licencia MIT está en `dictionary/LICENSE.txt`.

## Construir y verificar

```powershell
.\src\build.ps1 -Python python
.\tests\run_checks.ps1 -Python .\.venv\Scripts\python.exe
.\installer\build-installer.ps1 -ISCC 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' -Payload 'path-to-complete-payload'
```

Construya con Inno Setup 6.7 o posterior. Las pruebas utilizan muestras generadas y bibliotecas temporales aisladas. Cubren lectura, selección, páginas continuas, OCR, diccionarios, anotaciones, exportaciones, combinación de múltiples archivos y preferencias de idioma. Las cargas útiles del instalador incluyen catálogos de idiomas y excluyen `data`, `exports`, `.git` y artefactos de prueba.

## Declaración de autor y licencia.

Autor: XT (XuTao). Este proyecto fue desarrollado con la ayuda de grandes modelos de lenguaje y es completamente de código abierto bajo GNU AGPLv3; ver [LICENSE](LICENSE). Los componentes de terceros conservan sus propias licencias; ver [Third-party notices](第三方说明.txt).

Sin la autorización del autor, el autor no proporciona implementación comercial, personalización comercial ni soporte relacionado. Esta política de soporte no restringe los derechos otorgados por GNU AGPLv3 y no prohíbe el uso comercial permitido por esa licencia. El uso comercial aún debe cumplir con todas las licencias de componentes aplicables.

Sugerencias y contacto: [peekaboocatx@gmail.com](mailto:peekaboocatx@gmail.com).

## Agradecimientos

Gracias a [Hunan University of Science and Technology](https://www.hnust.edu.cn/), su [School of Computer Science and Engineering](https://computer.hnust.edu.cn/) y al Laboratorio Provincial Clave de Computación de Servicios y Tecnologías de Servicios de Software Novedosos de la provincia de Hunan por proporcionar un entorno para el estudio y la investigación.

## Alcance y traducciones

Esta aplicación se desarrolló de forma independiente y no es un producto oficial MAiMemo. No inicia sesión en MAiMemo ni carga libros de palabras automáticamente. La búsqueda sin conexión no es una traducción automática de oraciones completas. Es posible que sea necesario comprobar el OCR, el vocabulario poco común y los diseños de PDF complejos.

El texto de la interfaz traducido y los archivos README se prepararon con asistencia automatizada; las correcciones son bienvenidas en la dirección de contacto anterior. El archivo README en inglés es la base de documentación. Los identificadores de código, los nombres de archivos estables y las claves de registros almacenados utilizan nombres de proyectos consistentes; ver [Naming conventions](NAMING.md).
