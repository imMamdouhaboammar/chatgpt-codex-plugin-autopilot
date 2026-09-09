# Full Autopilot Release Playbook

Full Autopilot Publish means routine release actions may proceed without another confirmation after the user has authorized that mode. It does not mean bypassing fail-closed gates or publishing to channels the repository does not use.

## Before publication

Require a clean, identified repository and confirm the intended remote, package identity, version, default branch, and current release policy. Refuse to overwrite an existing immutable registry version. Never force-push unrelated history.

Run repository-native unit, integration, security, lint, package, install/uninstall, and domain acceptance checks. Run the generic plugin validator. Build the plugin ZIP twice from the same source and require equal SHA256. Inspect archive entries, size limits, public exclusions, policy URLs, branding, hooks/MCP boundaries, and secret-shaped content.

Commit release metadata before irreversible publication. Rebuild publish artifacts from that exact release commit when the repository's build permits it.

## npm when the target uses npm

npm is conditional, not a universal plugin requirement. If the target does publish npm and has no stronger project policy, prefer authenticated local-terminal publication. Keep registry tokens out of GitHub Actions and plugin configuration.

A strong release sequence is:

1. build and inspect the exact tarball
2. record SHA256, npm shasum, and package version
3. publish the local tarball using the intended dist-tag
4. query the registry for version and dist-tags
5. `npm pack <name>@<version>` into a clean directory
6. byte-compare the registry tarball against the locally published tarball
7. only then create/push the release tag that triggers artifact publication

If CI creates GitHub Releases, CI should retrieve the already-published registry artifact and compare it with its own deterministic build before attaching assets. CI must not be given npm publish credentials merely for convenience.

## GitHub when the target uses GitHub

Push the release commit and immutable tag only after the registry dependency, if any, is satisfied. Verify remote commit/tag SHAs. Wait for required CI/security/release workflows and inspect their actual conclusions.

The single authoritative release workflow for all versions is `.github/workflows/release.yml`, triggered on immutable `v*` tag pushes. It operates under least-privilege permissions by isolating read-only verification (`verify` job with `contents: read`) from publication (`publish` job with `contents: write`). The `verify` job checks tag-to-manifest version alignment, proves commit ancestry on default branch `main`, runs full test suites, directory listing validation, and self-checks, performs two independent deterministic builds with bitwise comparison, and stages verified assets. The `publish` job creates the release and executes post-publish verification by downloading the released assets and validating SHA256 checksums. The historical one-shot workflow `publish-v0.3.0.yml` is permanently retired.

Download GitHub Release assets after publication. Compare the npm asset to the registry artifact and the plugin ZIP to the locally deterministic build. Reinspect the downloaded ZIP rather than assuming upload preserved the intended file.

## Plugin Directory

Prepare the exact ZIP that passed the gate. Submit through the current official public Plugin Directory flow when the environment exposes it. A successful GitHub Release is not a successful Plugin Directory review. Report states separately: package prepared, uploaded/submitted, under review, approved, appealed, failed, or published.

If the submission interface cannot be automated from the available environment, stop only that channel after preparing and verifying the exact upload artifact. Do not claim public publication. Continue independent GitHub/npm release work when it was authorized and does not depend on directory approval.

## Post-publish evidence

Record at minimum:

- release commit SHA and tag
- plugin manifest version
- package version/dist-tag when relevant
- plugin ZIP SHA256
- package tarball SHA256/shasum/integrity when relevant
- total Skills/agents if the package exposes a generated catalog
- exact public exclusions checked
- test counts and required workflow conclusions
- artifact comparison result
- any non-blocking platform warning

Do not mark the task complete from build logs alone. Query the remote systems that now own the published state.
