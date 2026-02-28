# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Security & Secrets

**You have ZERO access to Doppler CLI.**

- ❌ Do NOT run `doppler secrets` or any doppler commands
- ✅ All credentials are injected by OpenClaw at startup
- ✅ If you need new credentials, message Builder with your requirement

Example:
```
Builder, I need access to Stripe API to handle payment webhooks.
Please add STRIPE_API_KEY to my environment.
```

Builder will add the secret to Doppler and restart the gateway. You'll have it automatically.
