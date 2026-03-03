# Aivar Email Spam Issues - Complete Fix

## Problems Identified

### 1. ✅ FIXED: UTF-8 Corruption in Subject
- **Issue:** Non-ASCII characters in subjects → "Ã Â£..." corruption
- **Fix:** ASCII-only subject enforcement added to AGENTS.md
- **Status:** Documented, awaits Aivar restart

### 2. ⚠️ TO FIX: Missing Sender Display Name
**Current:** `aivar.chudaikin@gmail.com`
**Should be:** `Aivar Chu <aivar.chudaikin@gmail.com>`

**Why it matters:**
- Email with no display name looks automated/bot-sent
- Major spam signal for filters
- Lower user trust

**How to fix:**
```bash
# When sending via gog CLI, add --from with display name:
gog gmail messages send \
  --from "Aivar Chu <aivar.chudaikin@gmail.com>" \
  --to recipient@example.com \
  --subject "Meeting Confirmation" \
  --body "..."
```

**Action needed:** Check if gog CLI supports `--from` with display name format

### 3. ⚠️ TO CHECK: Email Content Format

**Need to verify:**
- Is Aivar sending HTML or plain text?
- Are messages properly formatted?
- Any spam trigger words/patterns?

**Best practices:**
- Plain text preferred for transactional/scheduling emails
- If HTML: minimal formatting, avoid spam trigger patterns
- Proper paragraph breaks and readability
- No all-caps, minimal exclamation marks

### 4. ⚠️ TO MONITOR: Sending Patterns

**Good practice limits:**
- Max 100 emails/day from new sender
- Max 10 emails/hour to avoid burst detection
- Warm up period: start slow, increase gradually

**Current status:** Unknown - need to check Aivar's sending volume

### 5. ✅ AUTO-HANDLED: SPF/DKIM/DMARC
Gmail automatically handles authentication for @gmail.com addresses:
- SPF: Passes (gmail.com → _spf.google.com)
- DKIM: Auto-signed by Google
- DMARC: Gmail policy applies

## Immediate Actions

### For Builder (You)
1. ✅ Added ASCII-only subject rule
2. ⏳ Check if gog CLI supports display name in --from
3. ⏳ Add display name configuration to Aivar's setup

### For Aivar (Next Send)
1. Use English/ASCII subject lines only
2. Keep email body professional and clear
3. Avoid spam trigger words: "urgent", "free", "click here", excessive caps
4. Include context in body (don't just send bare links)

## Long-term Recommendations

### Week 1-2: Reputation Building
- Send only to people who've interacted with you
- Avoid cold outreach during warmup
- Monitor spam complaints (check Gmail sent folder for bounces)

### Ongoing: Content Quality
- Personalized greetings
- Clear call-to-action
- Proper signature with contact info
- Professional tone

### Technical Improvements
1. Add email signature to all Aivar sends
2. Configure display name properly
3. Monitor bounce/spam rates
4. Implement rate limiting (max 5-10/hour initially)

## Testing

Before sending to external recipients:
1. Send test email to yourself
2. Check spam folder
3. View source and verify headers
4. Confirm display name shows correctly
5. Verify subject is ASCII-only

## Current Status

- **Subject encoding:** ✅ Fixed (restart pending)
- **Display name:** ⚠️ Needs implementation
- **Content format:** ❓ Unknown (need to check)
- **Sending volume:** ❓ Unknown (need to monitor)
- **Authentication:** ✅ Handled by Gmail

## Next Steps

1. Restart Aivar to apply ASCII subject rule
2. Check gog CLI display name support
3. Add display name if supported
4. Monitor next few sends for spam classification
5. Adjust based on results
