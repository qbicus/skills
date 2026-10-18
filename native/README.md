# sqlite-vec Native Runtime Files

This directory contains the platform-specific `sqlite-vec` native runtime
binaries used by AiIndex together with the pinned upstream release archives
from which they were extracted.

These files are runtime dependencies/provenance artifacts only. They are not
AiIndex source code and should not normally be modified by hand.

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
├── win-x64/
│   └── vec0.dll
├── sqlite-vec-0.1.10-alpha.4-loadable-linux-aarch64.tar.gz
├── sqlite-vec-0.1.10-alpha.4-loadable-linux-x86_64.tar.gz
├── sqlite-vec-0.1.10-alpha.4-loadable-macos-aarch64.tar.gz
├── sqlite-vec-0.1.10-alpha.4-loadable-macos-x86_64.tar.gz
├── sqlite-vec-0.1.10-alpha.4-loadable-windows-x86_64.tar.gz
└── LICENSE-MIT
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

Native Windows ARM64 is not currently bundled because the pinned upstream
sqlite-vec release does not provide a Windows ARM64 binary.

## Source / provenance

The bundled binaries and archives originate from the official sqlite-vec
release artifacts pinned by AiIndex.

Current pinned upstream version:

```text
0.1.10-alpha.4
```

This repository intentionally keeps both:

- the original pinned upstream `.tar.gz` release archives; and
- the extracted `vec0` runtime library for each supported platform.

Keeping both makes the exact upstream artifacts used by AiIndex explicit and
preserves reproducible provenance for the extracted native libraries.

sqlite-vec is dual-licensed upstream under MIT or Apache-2.0. This repository
redistributes the bundled sqlite-vec artifacts under the MIT option; the
upstream MIT license is retained at `native/sqlite-vec/LICENSE-MIT`. See also
the root `THIRD_PARTY_NOTICES.md`.

## Git policy

Keep the pinned upstream sqlite-vec release archives, the extracted `vec0`
runtime binaries, and the sqlite-vec license tracked.

Do not add temporary extraction directories, unrelated downloaded versions, or
other generated native artifacts unless they are intentionally part of an
AiIndex runtime update.

## Updating sqlite-vec

When updating the native runtime:

1. Update the pinned sqlite-vec version in AiIndex.
2. Download the official upstream artifacts for the supported RIDs.
3. Keep the pinned upstream archives in `native/sqlite-vec/`.
4. Extract the required `vec0` binary for each supported platform.
5. Preserve the applicable upstream license file(s).
6. Rebuild and validate the AiIndex release artifacts.
7. Verify hybrid/vector search on at least one supported platform.
8. Update this README and `THIRD_PARTY_NOTICES.md` if the version, supported
   RIDs, provenance, or licensing changes.
