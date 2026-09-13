#define AppName "MemoIdx"
#define AppVersion "0.1.0"
#define Publisher "MemoIdx"
#define SourceRoot ".."
#define BinRoot "..\dist\windows"

[Setup]
AppId={{B0B2A62A-7A84-4E9E-9A45-6D3E5B8F6CF1}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#Publisher}
DefaultDirName={localappdata}\MemoIdx
DefaultGroupName=MemoIdx
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist\installer
OutputBaseFilename=install
Compression=lzma2
SolidCompression=yes
; Avoid extracting and executing the Setup engine from %TEMP%, which is
; blocked by Windows Application Control policies on some machines.
UseSetupLdr=no
WizardStyle=modern
ChangesEnvironment=yes
UninstallDisplayName=MemoIdx

[Files]
Source: "{#BinRoot}\memoidx.exe"; DestDir: "{app}\bin"; Flags: ignoreversion
Source: "{#BinRoot}\memoidx-init.exe"; DestDir: "{app}\bin"; Flags: ignoreversion
Source: "{#SourceRoot}\MemoIdx.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "{#SourceRoot}\memoidx\protocol.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "{#SourceRoot}\memoidx\memoidx-cli.md"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "{#SourceRoot}\memoidx\memoidx-scout.md"; DestDir: "{app}\docs"; Flags: ignoreversion

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}\bin"; Flags: preservestringtype; Check: NeedsAddPath

[Dirs]
[Icons]
Name: "{autoprograms}\MemoIdx\MemoIdx documentation"; Filename: "{app}\docs"
Name: "{autoprograms}\MemoIdx\Initialize current workspace"; Filename: "{app}\bin\memoidx-init.exe"; Parameters: "--workspace ""{code:GetWorkspace}"" --user-root ""{%USERPROFILE}\.memoidx"""

[Run]
Filename: "{app}\bin\memoidx-init.exe"; Parameters: "--workspace ""{code:GetWorkspace}"" --user-root ""{%USERPROFILE}\.memoidx"""; Description: "Initialize a workspace now"; Flags: postinstall skipifsilent unchecked

[UninstallDelete]
Type: dirifempty; Name: "{app}\bin"
Type: dirifempty; Name: "{app}\docs"

[Code]
function NeedsAddPath(): Boolean;
var
  ExistingPath: String;
begin
  if not RegQueryStringValue(HKEY_CURRENT_USER, 'Environment', 'Path', ExistingPath) then
    ExistingPath := '';
  Result := Pos(ExpandConstant('{app}\bin'), ExistingPath) = 0;
end;

var
  WorkspacePage: TInputDirWizardPage;

procedure InitializeWizard;
begin
  WorkspacePage := CreateInputDirPage(wpSelectDir,
    'Workspace initialization', 'Choose a workspace (optional)',
    'MemoIdx will create MemoIdx.md and agent adapters here.', False, '');
  WorkspacePage.Add('Workspace:');
  WorkspacePage.Values[0] := ExpandConstant('{src}');
end;

function GetWorkspace(Param: String): String;
begin
  Result := WorkspacePage.Values[0];
end;
