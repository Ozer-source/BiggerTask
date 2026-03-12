; ============================================================================
; BiggerTask - Installer Script for Inno Setup
; ============================================================================
; This script creates an installer (Installer.exe) that installs BiggerTask
; to C:\Program Files\BiggerTask and creates a desktop shortcut.
;
; Requirements:
; - Inno Setup installed (free from https://jrsoftware.org/isdl.php)
; - BiggerTask.exe in the dist/ folder
; - dist folder must be in the SAME folder as this .iss file
;
; Usage:
; 1. Install Inno Setup
; 2. Make sure dist/ folder is in same directory as this .iss file
; 3. Open this file (.iss) with Inno Setup
; 4. Click "Compile" (Ctrl+F9)
; 5. Output: Installer.exe (in same directory)
; ============================================================================

[Setup]
; Installer metadata
AppName=BiggerTask
AppVersion=1.0.0
AppPublisher=BiggerTask Development
AppPublisherURL=https://example.com
AppSupportURL=https://example.com
AppUpdatesURL=https://example.com

; Installation directory
DefaultDirName={pf}\BiggerTask
DefaultGroupName=BiggerTask

; Installer appearance
SetupIconFile=
WizardStyle=modern
WizardResizable=yes
ShowLanguageDialog=no

; Output
OutputDir=.
OutputBaseFilename=Installer

; Compression
Compression=lzma2
SolidCompression=yes

; Permissions
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=commandline

; Architecture
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64

; License (optional - comment out if no license file)
; LicenseFile={src}\LICENSE.txt

; ============================================================================
; LANGUAGES
; ============================================================================

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "de"; MessagesFile: "compiler:Languages\German.isl"

; ============================================================================
; INSTALLATION TYPES
; ============================================================================

[Types]
Name: "full"; Description: "Full installation"
Name: "compact"; Description: "Compact installation (no uninstaller)"
Name: "custom"; Description: "Custom Installation"; Flags: iscustom

[Components]
Name: "program"; Description: "BiggerTask Program"; Types: full compact custom; Flags: fixed
Name: "uninstaller"; Description: "Uninstaller"; Types: full custom
Name: "shortcut"; Description: "Desktop Shortcut"; Types: full compact custom; Flags: fixed

; ============================================================================
; FILES TO INSTALL
; ============================================================================

[Files]
; Copy BiggerTask.exe from dist/ folder to installation directory
Source: "dist\BiggerTask.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: program

; Create empty playbacks folder (handled by CreateDirs directive below)

; ============================================================================
; DIRECTORIES TO CREATE
; ============================================================================

[Dirs]
; Create playbacks folder in installation directory
Name: "{app}\playbacks"; Flags: uninsalwaysuninstall

; ============================================================================
; DESKTOP SHORTCUT
; ============================================================================

[Icons]
; Create desktop shortcut pointing to BiggerTask.exe
Name: "{userdesktop}\BiggerTask"; Filename: "{app}\BiggerTask.exe"; WorkingDir: "{app}"; Flags: createonlyiffileexists; Components: shortcut

; Create start menu shortcut (optional)
Name: "{group}\BiggerTask"; Filename: "{app}\BiggerTask.exe"; WorkingDir: "{app}"; Components: program

; Create uninstaller shortcut in Start Menu
Name: "{group}\Uninstall BiggerTask"; Filename: "{uninstallexe}"; Components: uninstaller

; ============================================================================
; RUN AFTER INSTALLATION
; ============================================================================

[Run]
; Launch BiggerTask after installation (optional - comment out to disable)
Filename: "{app}\BiggerTask.exe"; Description: "Launch BiggerTask now"; Flags: nowait postinstall skipifsilent; Components: program

; ============================================================================
; UNINSTALLATION
; ============================================================================

[UninstallDelete]
; Delete playbacks folder on uninstall
Type: dirifempty; Name: "{app}\playbacks"
; Delete app folder if empty
Type: dirifempty; Name: "{app}"

; ============================================================================
; INSTALLATION MESSAGE STRINGS (Optional Customization)
; ============================================================================

[CustomMessages]
en.WelcomeLabel1=Welcome to BiggerTask Setup
en.WelcomeLabel2=This will install BiggerTask - a macro recorder for Windows.
en.FinishedHeadingLabel=Installation Complete!
en.FinishedLabel=BiggerTask has been successfully installed.%n%nA shortcut has been created on your desktop for easy access.

de.WelcomeLabel1=Willkommen zum BiggerTask Setup
de.WelcomeLabel2=Dies wird BiggerTask - einen Makrorecorder für Windows - installieren.
de.FinishedHeadingLabel=Installation abgeschlossen!
de.FinishedLabel=BiggerTask wurde erfolgreich installiert.%n%nEine Verknüpfung wurde auf Ihrem Desktop erstellt.

; ============================================================================
; END OF INSTALLER SCRIPT
; ============================================================================
