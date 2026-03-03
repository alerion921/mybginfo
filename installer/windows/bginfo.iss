; MyBGInfo Inno Setup installer script
; Requires Inno Setup 6+ and PyInstaller output in ../../dist/bginfo/

[Setup]
AppName=MyBGInfo
AppVersion=1.0
AppPublisher=alerion921
AppPublisherURL=https://github.com/alerion921/mybginfo
DefaultDirName={pf}\MyBGInfo
DefaultGroupName=MyBGInfo
OutputBaseFilename=MyBGInfo-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Copy all PyInstaller bundled files
Source: "..\..\dist\bginfo\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Copy assets and config
Source: "..\..\assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\..\config\bginfo.json"; DestDir: "{app}\config"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\MyBGInfo"; Filename: "{app}\bginfo.exe"
Name: "{group}\Uninstall MyBGInfo"; Filename: "{uninstallexe}"
; Startup shortcut so it runs at Windows login
Name: "{userstartup}\MyBGInfo"; Filename: "{app}\bginfo.exe"

[Run]
; Run the application after installation completes
Filename: "{app}\bginfo.exe"; Description: "Launch MyBGInfo now"; Flags: nowait postinstall skipifsilent
