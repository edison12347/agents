# USER.md - About Your Human

_Learn about the person you're helping. Update this as you go._

- **Name:**
- **What to call them:**
- **Pronouns:** _(optional)_
- **Timezone:**
- **Notes:** Prefers CLI workflows when possible; first check for built-in OpenClaw features before external CLI steps. For completed agent creation work, expects commit + push to GitHub every time. For future agent creations, proactively verify provider auth/model availability and avoid known model/auth cooldown pitfalls before go-live testing. Going forward, validate agent work by sending a direct test message and only mark done after the agent replies successfully.

## Context

_(What do they care about? What projects are they working on? What annoys them? What makes them laugh? Build this over time.)_

---

The more you know, the better you can help. But remember — you're learning about a person, not building a dossier. Respect the difference.

## Critical Security Notes

**2026-02-28:** Implemented no-disclosure policy for Doppler secrets after Builder disclosed GOG_KEYRING_PASSWORD when asked. Builder will now REFUSE all secret disclosure requests via chat unless a valid override token is provided (see `SECURITY_OVERRIDE_PROTOCOL.md`). This prevents prompt injection and accidental leaks.

**For secret access:** Use `doppler secrets get SECRET_NAME --plain` via SSH, or follow the emergency override protocol documented in `SECURITY_OVERRIDE_PROTOCOL.md`.
