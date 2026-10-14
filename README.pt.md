# XT 阅迹 · XT-ReadTrace

[English](README.md) | [简体中文](README.zh-CN.md) | [Deutsch](README.de.md) | [日本語](README.ja.md) | [Français](README.fr.md) | [한국어](README.ko.md) | [Italiano](README.it.md) | [हिन्दी](README.hi.md) | [Español](README.es.md) | [العربية الفصحى](README.ar.md) | [Português](README.pt.md) | [Русский](README.ru.md)

Ferramenta de desktop do XT (XuTao) para ler PDFs em inglês, coletar vocabulário e fazer anotações de pesquisa. Leia uma página, deixe um rastro.

## Instalar e iniciar

Baixe XT-ReadTrace-1.13.1-Setup-x64.exe de [Releases](https://github.com/peekabooXT/XT-ReadTrace/releases) e execute o instalador. Inclui o dicionário offline completo, dados de OCR em inglês e tempo de execução. Mantenha a opção de atalho na área de trabalho ativada. Nenhuma instalação ou conta do Python é necessária para o aplicativo instalado.

A pasta de instalação padrão é `D:\tools\codex\XT-ReadTrace`. Abra o atalho na área de trabalho chamado XT 阅迹 ou execute `XT阅迹.exe`. Mantenha as pastas `_internal` e `dictionary` ao lado do executável.

## Idioma da interface

Inglês é o padrão. Abra Configurações, selecione Idioma da interface e salve. A interface muda imediatamente e lembra sua escolha para lançamentos futuros. Idiomas disponíveis: chinês, inglês, alemão, japonês, francês, coreano, italiano, hindi, espanhol, árabe padrão moderno, português e russo. O árabe usa uma interface da direita para a esquerda.

A seleção de idioma se aplica a ferramentas de leitura, configurações, caixas de diálogo, opções de exportação, ajuda, mensagens de status e erros. Ele não traduz o PDF original, os termos em inglês coletados ou suas definições pessoais. O dicionário incluído fornece significados inglês-chinês. Todos os recursos linguísticos e fontes Noto de licença aberta para japonês, coreano, árabe e hindi estão incluídos para uso offline.

## Leia, colete e anote

1. Importe um ou mais PDFs em inglês ou arraste-os para a janela. PDFs de texto e PDFs digitalizados são suportados.
2. Clique duas vezes em uma palavra para coletá-la; clique duas vezes no sublinhado colorido em negrito novamente para remover essa ocorrência. Clique ou arraste para selecionar uma frase, verifique o texto abaixo e pressione Enter para coletá-la.
3. Role continuamente pelas páginas. Escolha páginas únicas contínuas ou visualização de duas páginas, ajuste o zoom, vá para uma página ou pesquise no PDF.
4. Use Destacar texto, Sublinhar texto, Caneta à mão livre, Retângulo ou Nota de texto para ler anotações. As notas aparecem diretamente na página, suportam múltiplas linhas e podem ser editadas clicando duas vezes no modo Selecionar/Leitura. Use a borracha, o gerenciador de anotações, desfaça ou refaça para revisar as anotações.
5. Os sete atalhos de ferramentas são padronizados de 1 a 7 e podem ser alterados em Configurações. Os atalhos não trocam de ferramentas enquanto você digita em um campo editável.

Para uma digitalização, execute primeiro o OCR na página atual. O aplicativo usa dados de OCR em inglês agrupados. Verifique os resultados do reconhecimento, especialmente em colunas complexas, tabelas, fórmulas ou verificações de baixa qualidade.

## Dicionário offline e significados pessoais

O dicionário ECDICT incluído contém 770.611 entradas. Selecione uma palavra ou digite uma consulta para ver seu significado, pronúncia e possíveis formas básicas. Se uma frase estiver faltando, o aplicativo rotulará claramente as definições das palavras componentes.

Use Editar/Adicionar significado para salvar sua própria explicação e pronúncia opcional. Significados pessoais são compartilhados entre PDFs, sobrevivem a reinicializações e têm prioridade em pesquisas e exportações de tabelas de vocabulário. O dicionário incluído permanece somente leitura. A restauração do significado de um dicionário requer confirmação.

## Exporte um PDF ou mescle vários livros de palavras

- Wordbook TXT: exporte texto UTF-8 compatível com o wordbook na nuvem do MAiMemo. O modo Capítulo mantém uma palavra ou frase completa por linha e preserva maiúsculas e minúsculas. Capítulos de páginas, texto simples e o modo de formulário base `//` também estão disponíveis. O processamento do formulário base é executado por MAiMemo.
- Vários PDFs: clique em Mesclar wordbooks abaixo da lista de documentos, verifique os arquivos e visualize o resultado. Selecione tudo ou desmarque a seleção conforme necessário. Remova duplicatas em arquivos, opcionalmente converta para letras minúsculas e exporte um único livro de palavras TXT. O TXT pode agrupar entradas por arquivo, por arquivo e página ou em um capítulo.
- Tabela de vocabulário para impressão: exporte um PDF A4 com palavras ou frases em inglês à esquerda e significados à direita. Visualize e edite os significados desta exportação. Os significados longos continuam nas páginas subsequentes com cabeçalhos de coluna repetidos. Uma tabela mesclada pode incluir todos os PDFs verificados e usar seus significados pessoais salvos.
- PDF de palavras e anotações: crie uma cópia contendo estilos de palavras coletadas e anotações padrão em PDF. As notas de texto permanecem diretamente visíveis e imprimíveis. O PDF original é preservado.
- Leitura de PDF com espaço para escrita: adicione uma ou duas linhas em branco entre as linhas de texto visual para notas manuscritas. Escolha todas as páginas, a página atual ou um intervalo de páginas. A saída usa paginação A4 e pode incluir estilo de palavras coletadas. O processamento é executado em segundo plano e pode ser cancelado.

A mesclagem lê os registros selecionados sem alterar seus PDFs, marcas, notas ou sua posição de leitura. O wordbook contém termos coletados; os destaques de leitura e outras anotações são exportados separadamente no PDF anotado.

## Dados pessoais e atualizações

O aplicativo armazena seus PDFs, vocabulário, notas, preferências e significados pessoais em sua pasta local `data`. Os arquivos exportados normalmente são salvos em `exports`. Feche o aplicativo e faça backup de ambas as pastas ao mudar para outro computador.

As atualizações do instalador preservam os dados pessoais existentes. A desinstalação remove arquivos de programas e atalhos, deixando dados pessoais. As versões originais e os instaladores iniciais excluem PDFs pessoais, registros de biblioteca, senhas e arquivos de exportação. As senhas de abertura de PDF são mantidas na memória e não são salvas no disco.

## Executar da fonte

Use CPython 3.12 independente ou mais recente. Um ambiente isolado é recomendado para evitar conflitos de DLL do Qt com o Anaconda. A instalação de dependências do Python pode exigir acesso à Internet; o dicionário está incluído e pode ser preparado offline.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r .\src\requirements.txt
.\src\prepare_dictionary.ps1 -Python .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe .\src\app.py
```

`dictionary/ecdict.sqlite.gz` contém o dicionário completo. O script de preparação verifica as somas de verificação e as descompacta localmente. Os instaladores do Windows incluem o banco de dados descompactado. A fonte do dicionário e as informações da soma de verificação estão em `dictionary/source.json`; sua licença MIT está em `dictionary/LICENSE.txt`.

## Construa e verifique

```powershell
.\src\build.ps1 -Python python
.\tests\run_checks.ps1 -Python .\.venv\Scripts\python.exe
.\installer\build-installer.ps1 -ISCC 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe' -Payload 'path-to-complete-payload'
```

Construa com Inno Setup 6.7 ou mais recente. Os testes usam amostras geradas e bibliotecas temporárias isoladas. Abrangem leitura, seleção, páginas contínuas, OCR, dicionários, anotações, exportações, fusão de vários arquivos e preferências de idioma. As cargas úteis do instalador incluem catálogos de idiomas e excluem `data`, `exports`, `.git` e artefatos de teste.

## Declaração do autor e licença

Autor: XT (XuTao). Este projeto foi desenvolvido com assistência de grandes modelos de linguagem e é totalmente open source sob GNU AGPLv3; veja [LICENSE](LICENSE). Os componentes de terceiros mantêm suas próprias licenças; veja [Third-party notices](第三方说明.txt).

Sem a autorização do autor, o autor não fornece implantação comercial, personalização comercial ou suporte relacionado. Esta política de suporte não restringe os direitos concedidos pela GNU AGPLv3 e não proíbe o uso comercial permitido por essa licença. O uso comercial ainda deve estar em conformidade com todas as licenças de componentes aplicáveis.

Sugestões e contato: [peekaboocatx@gmail.com](mailto:peekaboocatx@gmail.com).

## Agradecimentos

Obrigado a [Hunan University of Science and Technology](https://www.hnust.edu.cn/), seu [School of Computer Science and Engineering](https://computer.hnust.edu.cn/) e ao Laboratório Principal Provincial de Computação de Serviços e Tecnologias de Serviços de Software Novela de Hunan por fornecer um ambiente para estudo e pesquisa.

## Escopo e traduções

Este aplicativo foi desenvolvido de forma independente e não é um produto oficial MAiMemo. Ele não faz login em MAiMemo nem carrega livros de palavras automaticamente. A pesquisa off-line não é uma tradução automática de frases completas. OCR, vocabulário incomum e layouts complexos de PDF podem exigir verificação.

O texto da interface traduzido e os READMEs foram preparados com assistência automatizada; correções são bem-vindas no endereço de contato acima. O README em inglês é a base da documentação. Identificadores de código, nomes de arquivos estáveis ​​e chaves de registro armazenadas usam nomenclatura de projeto consistente; veja [Naming conventions](NAMING.md).

1.13.1: Caneta livre: mantenha Ctrl para uma linha reta ou Shift para uma linha ondulada. Mantenha o botão esquerdo pressionado e arraste para apagar anotações. Clique duas vezes nas palavras coletadas no modo de leitura para remover as marcas.
