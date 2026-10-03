# Windows signing

The current preview installer is unsigned. SmartScreen reputation cannot be reliably changed through app code, file naming or a checksum.

For a signed release, obtain a trusted Windows code-signing certificate or approved cloud signing service. Sign the compiled bootstrap before appending the payload, then sign the final installer including its payload with a SHA-256 timestamp from the signing provider. Verify the final signature and test extraction after signing; appended-payload readers must account for an Authenticode certificate table after the trailer before this workflow can ship.

Never commit private certificates, PFX files, passwords or service credentials. Supply them through protected signing infrastructure. Publish the final signed file's checksum. Do not disable SmartScreen or remove security settings during setup.

Signing alone does not guarantee SmartScreen reputation or immediate removal of every warning. Unsigned previews must be labeled accurately.
