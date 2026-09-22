# Avalonia Checklist

Use this checklist when an `nf-spec`, `nf-design`, or `nf-tasks` pass involves Avalonia UI.

## Spec
- Target OS list is explicit
- Main windows/dialogs are listed
- Navigation model is clear
- Platform-specific behavior is called out
- Packaging/distribution expectations are recorded

## Design
- View/viewmodel boundaries are clear
- Dispatcher/threading rules are explicit
- Dialog and window ownership is defined
- Styling/resource strategy is defined
- Platform abstractions are identified
- Test boundaries are identified

## Tasks
- Shell/bootstrap work is separated from feature screens
- Shared resource or theme changes are dependency-aware
- Platform adapter work is isolated
- Packaging tasks exist if needed
- UI verification tasks exist
