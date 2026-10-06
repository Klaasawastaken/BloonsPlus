# Bloons+ Preview 46

## VM setup ownership and durable repair state

- Recheck setup-job ownership after the awaited guest idle probe. Two concurrent update requests now share one installation instead of launching two.
- Keep host start requests queued while VM setup/update runs, including ownership claimed during an awaited game-status probe. Existing pause/stop controls remain available; the queued dispatcher resumes after setup finishes.
- Flush setup-state updates to a unique temporary file before atomic replacement. Failed writes, flushes or replacement preserve the prior state and clean temporary files. Non-object cache shapes are ignored rather than spread into setup options.

Offline reproduction showed two installers before the ownership fix. Checks now cover concurrent updates, setup beginning during the probe, queued start ownership, and atomic-write failures. The existing explicit-idle update guard still passes. No VM settings, SSH privileges or game saves were edited by these checks.

Clean Windows installation without existing prerequisites remains unverified. Includes earlier held-placement, checkpoint and upgrade-unlock fixes. This is a preview; V1.0 is not complete.
