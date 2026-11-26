# Executive Summary PDF Branding Override

Optional project-specific branding for the `nf-executive-summary` skill.

To override global/default PDF styling, place a branding reference PDF here as:

```text
.ai/templates/executive-summary/reference.pdf
```

The skill uses the PDF only as a visual reference (colors, logo/mark imagery, typography hierarchy, page treatment, spacing). It never writes into or modifies the reference PDF.

Derived style data is generated locally under:

```text
.ai/cache/executive-summary/
```

The cache records the reference PDF SHA-256. Replacing/changing `reference.pdf` invalidates the cache automatically. Embedded font binaries are never extracted or redistributed.
