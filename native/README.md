# sqlite-vec Native Runtime Files

This directory contains the platform-specific `sqlite-vec` native runtime binaries used by AiIndex.

These files are runtime dependencies only. They are not AiIndex source code and should not normally be modified by hand.

## Expected layout

```text
native/sqlite-vec/
├── linux-arm64/
│   └── vec0.so
├── linux-x64/
│   └── vec0.so
├── osx-arm64/
│   └── vec0.dylib
├── osx-x64/
│   └── vec0.dylib
└── win-x64/
    └── vec0.dll
```

AiIndex resolves the native extension from:

```text
~/.ai/native/sqlite-vec/<rid>/
```

or on Windows:

```text
%USERPROFILE%\.ai\native\sqlite-vec\<rid>\
```

## Supported runtime identifiers

The currently supported AiIndex release targets are:

- `win-x64`
- `linux-x64`
- `linux-arm64`
- `osx-x64`
- `osx-arm64`

Native Windows ARM64 is not currently bundled because the pinned upstream sqlite-vec release does not provide a Windows ARM64 binary.

## Source / provenance

The bundled binaries originate from the official sqlite-vec release artifacts pinned by AiIndex.

Current pinned upstream version:

```text
0.1.10-alpha.4
```

The original downloaded archives are not required after extraction and should not be committed to this framework.

## Git policy

The platform runtime folders are installation payloads and may be excluded from Git when binaries are distributed through release assets.

Keep this README tracked so the expected directory structure, provenance, and supported RIDs remain documented.

## Updating sqlite-vec

When updating the native runtime:

1. Update the pinned sqlite-vec version in AiIndex.
2. Download the official upstream artifacts for the supported RIDs.
3. Extract only the required `vec0` binary for each platform.
4. Rebuild and validate the AiIndex release artifacts.
5. Verify hybrid/vector search on at least one supported platform.
6. Update this README if the supported RIDs or pinned version change.
