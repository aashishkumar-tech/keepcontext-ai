# VS Code Extension Release Checklist

Use this checklist before sharing the KeepContext AI extension with users.

## 1. Backend Wiring

- [ ] Backend health URL returns healthy.
- [ ] Extension setting `keepcontext.apiUrl` points to live backend URL.
- [ ] Extension can load memories from live backend.

Recommended value for current deployment:

- `keepcontext.apiUrl`: `http://13.232.100.178`

How to set in VS Code (Settings JSON):

```json
{
  "keepcontext.apiUrl": "http://13.232.100.178"
}
```

## 2. Feature Smoke Test (Extension UI)

- [ ] `KeepContext: Store Memory` succeeds.
- [ ] `KeepContext: Query Context` returns results.
- [ ] `KeepContext: Ask Question` returns enriched response.
- [ ] `KeepContext: Run Agent Workflow` returns panel output.
- [ ] Sidebar memories load and refresh works.

## 3. Build VSIX

Run from `vscode-extension/`:

```bash
npm ci
npm run compile
npm run package
```

Expected output file:

- `keepcontext-ai-0.1.0.vsix`

## 4. Install VSIX Locally (Validation)

```bash
code --install-extension keepcontext-ai-0.1.0.vsix --force
```

Then open a clean VS Code window/profile and re-run smoke tests.

## 5. Share VSIX to Users

- [ ] Upload `.vsix` to shared drive/release page.
- [ ] Share install command.
- [ ] Share required setting `keepcontext.apiUrl`.

Install command for users:

```bash
code --install-extension keepcontext-ai-0.1.0.vsix
```

## 6. Known Launch Constraints

- API currently uses HTTP, not HTTPS.
- Anyone with endpoint access can call API unless additional auth is added.
- Public IP can change if EC2 is stopped and started.

## 7. Go/No-Go

Go only if sections 1-5 are complete and smoke tests pass on a clean install.
