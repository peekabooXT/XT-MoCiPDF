; Compile with Inno Setup 6.7+; payload contains no data/exports/work/.git.
#ifndef PayloadDir
  #define PayloadDir ".."
#endif
#ifndef BuildVersion
  #define BuildVersion "1.6.0"
#endif

[Setup]
AppId={{D7E6B964-0F14-45C2-8572-4378D6CDB513}
AppName=XT 墨词
AppVersion={#BuildVersion}
AppPublisher=XT (XuTao)
AppPublisherURL=https://github.com/peekabooXT/XT-MoCiPDF
AppSupportURL=https://github.com/peekabooXT/XT-MoCiPDF/issues
DefaultDirName={code:DefaultInstallDir}
DefaultGroupName=XT 墨词
DisableProgramGroupPage=yes
DisableDirPage=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19041
OutputBaseFilename=XT-MoCiPDF-{#BuildVersion}-Setup-x64
SetupIconFile={#PayloadDir}\icon.ico
UninstallDisplayIcon={app}\icon.ico
VersionInfoDescription=XT 墨词 Windows 安装包
VersionInfoProductName=XT 墨词
VersionInfoVersion={#BuildVersion}.0
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
UsePreviousTasks=yes

[Languages]
Name: "chinesesimplified"; MessagesFile: "ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "快捷方式："

[Files]
Source: "{#PayloadDir}\XT墨词.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\icon-preview.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#PayloadDir}\dictionary\ecdict.sqlite"; DestDir: "{app}\dictionary"; Flags: ignoreversion
Source: "{#PayloadDir}\dictionary\source.json"; DestDir: "{app}\dictionary"; Flags: ignoreversion
Source: "{#PayloadDir}\dictionary\LICENSE.txt"; DestDir: "{app}\dictionary"; Flags: ignoreversion
Source: "{#PayloadDir}\tessdata\eng.traineddata"; DestDir: "{app}\tessdata"; Flags: ignoreversion
Source: "{#PayloadDir}\src\*.py"; DestDir: "{app}\src"; Flags: ignoreversion
Source: "{#PayloadDir}\src\*.ps1"; DestDir: "{app}\src"; Flags: ignoreversion
Source: "{#PayloadDir}\src\requirements.txt"; DestDir: "{app}\src"; Flags: ignoreversion
Source: "{#PayloadDir}\tests\*.py"; DestDir: "{app}\tests"; Flags: ignoreversion
Source: "{#PayloadDir}\tests\*.ps1"; DestDir: "{app}\tests"; Flags: ignoreversion
Source: "{#PayloadDir}\installer\*.iss"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#PayloadDir}\installer\*.ps1"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#PayloadDir}\installer\*.isl"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#PayloadDir}\installer\*.json"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#PayloadDir}\installer\*.txt"; DestDir: "{app}\installer"; Flags: ignoreversion
Source: "{#PayloadDir}\licenses\*"; DestDir: "{app}\licenses"; Flags: ignoreversion
Source: "{#PayloadDir}\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\使用说明.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\第三方说明.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\验证记录.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\Example.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\精读导出示例.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\单词释义表导出示例.pdf"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\XT 墨词"; Filename: "{app}\XT墨词.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
Name: "{group}\卸载 XT 墨词"; Filename: "{uninstallexe}"
Name: "{autodesktop}\XT 墨词"; Filename: "{app}\XT墨词.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\XT墨词.exe"; Description: "启动 XT 墨词"; Flags: nowait postinstall skipifsilent

[Code]
function DefaultInstallDir(Param: String): String;
begin
  if DirExists('D:\tools\codex\XT-MoCiPDF') then
    Result := 'D:\tools\codex\XT-MoCiPDF'
  else if DirExists('D:\') then
    Result := 'D:\tools\codex\XT-MoCiPDF'
  else
    Result := ExpandConstant('{localappdata}\XT-MoCiPDF');
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Directory: String;
  I: Integer;
begin
  Result := '';
  Directory := WizardDirValue;
  for I := 1 to Length(Directory) do
    if Ord(Directory[I]) > 127 then
    begin
      Result := '请选择仅含英文字母、数字或符号的安装路径，以便离线 OCR 正常读取字库。';
      Exit;
    end;
end;

procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    '安装 XT 墨词：英文 PDF 精读、离线查词与词本工具。' + #13#10 + #13#10 +
    '安装包包含完整英汉词典和英文 OCR 字库，安装后无需联网下载。' + #13#10 + #13#10 +
    '升级时请选择原安装目录；已有 data 和 exports 文件夹会保留。';
end;

// No UninstallDelete entries: user data/exports are never removed.
