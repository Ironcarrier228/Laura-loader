[Setup]
AppName=LauraLoader
AppVersion=1.0
DefaultDirName={pf}\LauraLoader
DefaultGroupName=LauraLoader
OutputDir=output
OutputBaseFilename=LauraSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=icon.ico
PrivilegesRequired=admin

[Files]
Source: "dist\LauraLoader.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\LauraLoader"; Filename: "{app}\LauraLoader.exe"
Name: "{commondesktop}\LauraLoader"; Filename: "{app}\LauraLoader.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные задачи:"

[Run]
Filename: "{app}\LauraLoader.exe"; Description: "Запустить LauraLoader"; Flags: nowait postinstall skipifsilent