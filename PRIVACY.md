# Privacy

Last updated: 2026-08-13

Plugin Autopilot is a skills-only developer tool. It does not operate a publisher-hosted backend, user account service, telemetry collector, analytics endpoint, advertising service, or remote data store.

## Data collected by the publisher

None through the Plugin itself. The publisher does not receive, store, sell, or retain prompts, repository contents, source code, credentials, or generated release artifacts through a Plugin Autopilot service because no such service is operated.

## Data used during a workflow

When a user asks ChatGPT or Codex to inspect a repository, file, build output, or connected developer tool, that material may be processed by the host and by tools the user or workspace has made available. Plugin Autopilot provides instructions for that workflow but does not create an additional network destination for the data.

Users should not place reusable secrets in plugin manifests, Skill files, release archives, support reports, or public test fixtures. Credentials required by external services should remain in the host's approved credential store, environment variables, or CI secret storage.

## Third-party services

ChatGPT, Codex, GitHub, CI providers, registries, hosting services, or other tools a user chooses to invoke are separate services with their own terms and privacy practices. Plugin Autopilot does not silently connect to those services on its own.

## Retention

Publisher retention through Plugin Autopilot: none. Files or logs created in the user's repository, local environment, ChatGPT/Codex host, CI provider, or connected service follow that environment's retention settings and are outside this repository's control.

## User controls

Users can stop using, disable, or uninstall the Plugin and can revoke access to any connected tools through the relevant host or service. Repository artifacts produced by the workflow remain under the user's repository and filesystem controls.

For privacy questions or a suspected documentation mismatch, use the public support channel described in `SUPPORT.md` without posting credentials or private repository contents.
