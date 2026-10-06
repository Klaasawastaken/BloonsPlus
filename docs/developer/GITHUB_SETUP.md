# Developing Bloons+

This repository contains the current Windows app, VM setup scripts, modified AutoBTD6 runner,
recorded routes, route tools, interface assets, and reference engine sources.

## Run from source

Install Git, Node.js, Python, and the Microsoft Visual C++ x64 Redistributable on Windows.
BTD6 itself must be owned and installed through Steam. VM operation also requires App Sandbox,
a Windows installation image, and hardware virtualization.

```powershell
git clone https://github.com/Klaasawastaken/BloonsPlus.git
cd BloonsPlus
npm ci
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-installer.txt
Copy-Item autobtd6\userconfig.example.json autobtd6\userconfig.json
npm run app
```

The settings/setup interface handles VM provisioning. Sign in to Steam inside the VM when asked.
Steam credentials, SSH keys, game saves, local progress, runtime dependencies, and build output
are deliberately excluded from version control. Existing users should preserve their own
`autobtd6/userconfig.json` instead of replacing it with the example.

## Updates

Commit source changes and push them to `main`. Pulling changes updates a source checkout;
installed EXE copies and the guest VM require their own application update/deployment step.
The repository does not automatically publish installers or update installed apps.

To build the current Windows installer after setting up dependencies:

```powershell
.\.venv\Scripts\python.exe installer/make-installer.py
```

The output is `dist/BloonsPlusSetup.exe`. Publish installers as GitHub Release assets rather
than adding `dist` to Git. Installer builds depend on the local Python base installation,
Electron runtime downloaded by npm, and the Windows .NET Framework C# compiler.

For a release build, pass its exact planned tag explicitly:

```powershell
.\.venv\Scripts\python.exe installer/make-installer.py --release-version v0.1.4-preview.99
```

This stamps the staged app and native inventory with `0.1.4-preview.99`, leaving
the development checkout's version unchanged. The installer and installed
controller report that package identity, rather than the latest online release.
Without the option, the builder retains the development package version. Invalid
version input is rejected before replacing staging. Use the actual intended tag;
the example does not publish a release or certify full 1.0 readiness.

## Current limitations

Route availability does not guarantee a victory. Converted strategies, recovery placement,
and boss event execution still need validation in the installed game version. The boss route
generator currently derives a draft from an ordinary map route; it is not a complete boss
strategy. See `TODO.md` and the source for unfinished features.

Third-party engines and route sources retain their original licenses and attribution files.
Their nested Git history is not required to run Bloons+; their working source is included.
