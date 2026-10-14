; Compile with Inno Setup 6.7+; payload contains no data/exports/work/.git.
#ifndef PayloadDir
  #define PayloadDir ".."
#endif
#ifndef BuildVersion
  #define BuildVersion "1.13.2"
#endif

[Setup]
AppId={{D7E6B964-0F14-45C2-8572-4378D6CDB513}
AppName=XT 阅迹
AppVersion={#BuildVersion}
AppPublisher=XT (XuTao)
AppPublisherURL=https://github.com/peekabooXT/XT-ReadTrace
AppSupportURL=https://github.com/peekabooXT/XT-ReadTrace/issues
DefaultDirName={code:DefaultInstallDir}
DefaultGroupName=XT 阅迹
DisableProgramGroupPage=yes
DisableDirPage=no
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.19041
OutputBaseFilename=XT-ReadTrace-{#BuildVersion}-Setup-x64
SetupIconFile={#PayloadDir}\icon.ico
UninstallDisplayIcon={app}\icon.ico
VersionInfoDescription=XT 阅迹 Windows 安装包
VersionInfoProductName=XT 阅迹
VersionInfoVersion={#BuildVersion}.0
Compression=lzma2/normal
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=no
UsePreviousGroup=no
UsePreviousTasks=yes
UsePreviousLanguage=no
LanguageDetectionMethod=none
ShowLanguageDialog=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "ChineseSimplified.isl"

[CustomMessages]
english.Uninstall=Uninstall XT 阅迹
chinesesimplified.Uninstall=卸载 XT 阅迹
english.Launch=Launch XT 阅迹
chinesesimplified.Launch=启动 XT 阅迹
english.DataFailed=Cannot migrate reading data. Check disk space and permissions. Original data is preserved.
chinesesimplified.DataFailed=文档数据迁移失败，请检查磁盘空间和权限；原数据保留在原位置。
english.CreateDesktop=Create a desktop shortcut
chinesesimplified.CreateDesktop=创建桌面快捷方式
english.CreateFailed=Cannot create the installation folder. Existing reading data remains in its original location.
chinesesimplified.CreateFailed=无法创建新安装目录，原有文档数据保留在原位置。
english.ExportFailed=Cannot migrate exported files. Original exports are preserved.
chinesesimplified.ExportFailed=导出文件迁移失败，原导出文件仍保留在原位置。
english.AsciiPath=Choose an installation path using ASCII characters so offline OCR can read its data.
chinesesimplified.AsciiPath=请选择仅含英文字母、数字或符号的安装路径，以便离线 OCR 正常读取字库。
english.Shortcuts=Shortcuts:
chinesesimplified.Shortcuts=快捷方式：
english.MoveFailed=Cannot complete reading-data migration. Original data is preserved.
chinesesimplified.MoveFailed=无法完成文档目录迁移，原数据保留在原位置。

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktop}"; GroupDescription: "{cm:Shortcuts}"

[Files]
Source: "{#PayloadDir}\XT阅迹.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\icon-preview.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#PayloadDir}\dictionary\ecdict.sqlite"; DestDir: "{app}\dictionary"; Flags: ignoreversion
Source: "{#PayloadDir}\dictionary\source.json"; DestDir: "{app}\dictionary"; Flags: ignoreversion
Source: "{#PayloadDir}\dictionary\LICENSE.txt"; DestDir: "{app}\dictionary"; Flags: ignoreversion
Source: "{#PayloadDir}\tessdata\eng.traineddata"; DestDir: "{app}\tessdata"; Flags: ignoreversion
Source: "{#PayloadDir}\locales\*.json"; DestDir: "{app}\locales"; Flags: ignoreversion
Source: "{#PayloadDir}\fonts\*"; DestDir: "{app}\fonts"; Flags: ignoreversion
Source: "{#PayloadDir}\icons\*"; DestDir: "{app}\icons"; Flags: ignoreversion
Source: "{#PayloadDir}\src\*.py"; DestDir: "{app}\src"; Flags: ignoreversion
Source: "{#PayloadDir}\src\*.ps1"; DestDir: "{app}\src"; Flags: ignoreversion
Source: "{#PayloadDir}\src\requirements.txt"; DestDir: "{app}\src"; Flags: ignoreversion
Source: "{#PayloadDir}\src\version_info.txt"; DestDir: "{app}\src"; Flags: ignoreversion
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
Source: "{#PayloadDir}\README.*.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\NOTICE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\NAMING.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\使用说明.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\第三方说明.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\验证记录.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\Example.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\精读导出示例.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\单词释义表导出示例.pdf"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#PayloadDir}\论文批注导出示例.pdf"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\XT 阅迹"; Filename: "{app}\XT阅迹.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:Uninstall}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\XT 阅迹"; Filename: "{app}\XT阅迹.exe"; WorkingDir: "{app}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\XT阅迹.exe"; Description: "{cm:Launch}"; Flags: nowait postinstall skipifsilent

[Code]
var
  PreviousDirectory: String;

function InitializeSetup: Boolean;
begin
  RegQueryStringValue(HKCU,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{D7E6B964-0F14-45C2-8572-4378D6CDB513}_is1',
    'InstallLocation', PreviousDirectory);
  PreviousDirectory := RemoveBackslashUnlessRoot(PreviousDirectory);
  Result := True;
end;

function CopyReadingFiles(SourceDirectory, TargetDirectory: String): Boolean;
var
  Entry: TFindRec;
  SourcePath, TargetPath: String;
begin
  Result := ForceDirectories(TargetDirectory);
  if not Result then Exit;
  if FindFirst(AddBackslash(SourceDirectory) + '*', Entry) then
  begin
    try
      repeat
        if (Entry.Name <> '.') and (Entry.Name <> '..') and
           ((Entry.Attributes and $400) = 0) then
        begin
          SourcePath := AddBackslash(SourceDirectory) + Entry.Name;
          TargetPath := AddBackslash(TargetDirectory) + Entry.Name;
          if (Entry.Attributes and FILE_ATTRIBUTE_DIRECTORY) <> 0 then
            Result := CopyReadingFiles(SourcePath, TargetPath)
          else if not FileExists(TargetPath) then
            Result := FileCopy(SourcePath, TargetPath, True);
          if not Result then Exit;
        end;
      until not FindNext(Entry);
    finally
      FindClose(Entry);
    end;
  end;
end;

function RemovePreviousShortcuts(Directory: String): Boolean;
var
  Entry: TFindRec;
  Path: String;
  Shell, Link: Variant;
begin
  Result := False;
  if FindFirst(AddBackslash(Directory) + '*', Entry) then
  begin
    try
      repeat
        if (Entry.Name <> '.') and (Entry.Name <> '..') and
           ((Entry.Attributes and $400) = 0) then
        begin
          Path := AddBackslash(Directory) + Entry.Name;
          if (Entry.Attributes and FILE_ATTRIBUTE_DIRECTORY) <> 0 then
          begin
            if RemovePreviousShortcuts(Path) then
            begin
              Result := True;
              RemoveDir(Path); // Only empty folders containing retired links.
            end;
          end
          else if CompareText(ExtractFileExt(Path), '.lnk') = 0 then
          begin
            try
              Shell := CreateOleObject('WScript.Shell');
              Link := Shell.CreateShortcut(Path);
              if CompareText(RemoveBackslashUnlessRoot(ExtractFileDir(Link.TargetPath)),
                             PreviousDirectory) = 0 then
                if DeleteFile(Path) then Result := True;
            except
              Log('Could not inspect a previous shortcut.');
            end;
          end;
        end;
      until not FindNext(Entry);
    finally
      FindClose(Entry);
    end;
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and (PreviousDirectory <> '') and
     (CompareText(PreviousDirectory, RemoveBackslashUnlessRoot(ExpandConstant('{app}'))) <> 0) then
  begin
    RemovePreviousShortcuts(ExpandConstant('{userdesktop}'));
    RemovePreviousShortcuts(ExpandConstant('{userprograms}'));
  end;
end;

function DefaultInstallDir(Param: String): String;
begin
  if DirExists('D:\tools\codex\XT-ReadTrace') then
    Result := 'D:\tools\codex\XT-ReadTrace'
  else if DirExists('D:\') then
    Result := 'D:\tools\codex\XT-ReadTrace'
  else
    Result := ExpandConstant('{localappdata}\XT-ReadTrace');
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Directory, Staging: String;
  I: Integer;
begin
  Result := '';
  Directory := WizardDirValue;
  for I := 1 to Length(Directory) do
    if Ord(Directory[I]) > 127 then
    begin
      Result := CustomMessage('AsciiPath');
      Exit;
    end;
  if (PreviousDirectory <> '') and
     (CompareText(PreviousDirectory, RemoveBackslashUnlessRoot(Directory)) <> 0) then
  begin
    // Stage the entire library before making it visible to the new application.
    // Existing libraries at the destination take precedence and are not merged.
    if DirExists(PreviousDirectory + '\data') and not DirExists(Directory + '\data') then
    begin
      if not ForceDirectories(Directory) then
      begin
        Result := CustomMessage('CreateFailed');
        Exit;
      end;
      I := 0;
      repeat
        I := I + 1;
        Staging := Directory + '\.readtrace-upgrade-' + IntToStr(I);
      until not DirExists(Staging) and not FileExists(Staging);
      if not CopyReadingFiles(PreviousDirectory + '\data', Staging) then
      begin
        Result := CustomMessage('DataFailed');
        Exit;
      end;
      if not RenameFile(Staging, Directory + '\data') then
      begin
        Result := CustomMessage('MoveFailed');
        Exit;
      end;
    end;
    if DirExists(PreviousDirectory + '\exports') and
       not CopyReadingFiles(PreviousDirectory + '\exports', Directory + '\exports') then
      Result := CustomMessage('ExportFailed');
  end;
end;

procedure InitializeWizard;
begin
  if ActiveLanguage = 'english' then
    WizardForm.WelcomeLabel2.Caption := 'Install XT 阅迹: English PDF reading, offline dictionary and vocabulary notes.' + #13#10 + #13#10 + 'Includes the complete offline dictionary, English OCR and 12 interface languages. Existing reading data is preserved.'
  else WizardForm.WelcomeLabel2.Caption :=
    '安装 XT 阅迹：英文 PDF 精读、离线查词与词本工具。' + #13#10 + #13#10 +
    '安装包包含完整英汉词典和英文 OCR 字库，安装后无需联网下载。' + #13#10 + #13#10 +
    '新安装目录中的已有数据会保留；从已登记版本升级时自动迁移文档、批注和设置。';
end;

// No UninstallDelete entries: user data/exports are never removed.
