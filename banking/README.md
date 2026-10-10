# Enable Banking: personal ING Bank Śląski transaction downloads

Read-only (AIS) access to your own ING accounts for household budgeting, via
[Enable Banking](https://enablebanking.com). Everything runs **on your own computer**;
secrets and captures live in `~/.enable-banking/` (override with `EB_HOME`), never in this repo.

```bash
pip install -r banking/requirements.txt
```

`M` = manual (you), `A` = automated by `ebank.py`.

## 1. Create an Enable Banking account (M)
Go to <https://enablebanking.com/sign-in/>, enter your email, click the login link.
Open the [Applications dashboard](https://enablebanking.com/cp/applications).

## 2. Register a production application
1. **(A)** Generate the signing key and certificate:
   ```bash
   python3 banking/ebank.py keygen --cn "<your-name> household budgeting"
   # -> ~/.enable-banking/private.pem (secret) and public.crt (upload)
   ```
   (The control panel can also generate the key in the browser. If you use that, save the
   downloaded `.pem` as `~/.enable-banking/private.pem`.)
2. **(A)** Serve the privacy/terms pages while registering:
   ```bash
   python3 -m http.server 8765 --directory banking/pages
   ```
3. **(M)** In the dashboard, register a new application:

   | Field | Value |
   |---|---|
   | Environment | PRODUCTION |
   | Access | Account information (AIS) |
   | Certificate | `~/.enable-banking/public.crt` |
   | Redirect URL | `https://localhost:8766/callback` |
   | Privacy policy | `http://localhost:8765/privacy.html` |
   | Terms | `http://localhost:8765/terms.html` |
   | Data-protection email | your email |

   Review and accept the terms. If the form rejects localhost URLs, publish the two pages anywhere
   public (e.g. a GitHub Pages gist) and use those URLs instead.
4. **(A)** Save the application ID:
   ```bash
   echo '<application-id>' > ~/.enable-banking/app_id && chmod 600 ~/.enable-banking/app_id
   ```

## 3. Link your own ING accounts (M)
In the application's page, use **Activate by linking accounts**: Poland → ING Bank Śląski → personal.
Log in to ING, complete SCA, select accounts, approve. This activates the app in restricted
production mode (only your own accounts).

Check the app works:
```bash
python3 banking/ebank.py banks      # lists Polish banks and their max consent length
```

## 4. Create a reusable API session (A + M)
Account linking (step 3) does **not** give the API a session. Create one:
```bash
python3 banking/ebank.py authorize            # --bank to override if ING's name doesn't match uniquely
```
The script calls `POST /auth`, prints/opens the ING URL. **(M)** approve in ING. The browser then
lands on `https://localhost:8766/callback?code=...&state=...` and shows a connection error — that is
expected. Paste that URL into the prompt; the script verifies `state`, calls `POST /sessions`
and saves `~/.enable-banking/session.json` (account UIDs + consent expiry). The code is single-use
and short-lived, so paste it promptly.

Non-interactive variant (e.g. when an agent runs it remotely): `authorize --start` prints the URL and
saves the pending state; `authorize --finish '<callback URL>'` completes it.

```bash
python3 banking/ebank.py accounts             # session status, accounts, consent expiry
```

## 5. Download transactions (A)
```bash
python3 banking/ebank.py download --month 2026-09
python3 banking/ebank.py download --date 2026-09-15
python3 banking/ebank.py download --date-from 2026-09-01 --date-to 2026-09-30
```
Each run writes `~/.enable-banking/captures/<range>_<utc-stamp>/`:
- `raw/<account>_pNNN.json` — every API page as returned
- `transactions.csv` — one row per transaction: dates, status, amount/currency/signed amount,
  counterparty, creditor/debtor, description, balance after, MCC, references, plus `raw_json`
- `manifest.json` — per-account pages/counts/errors

**Only a manifest with `"complete": true` is a successful download.** The script exits `2` if any
account failed (all pages are still saved for inspection).

## 6. Renew consent
Consent lasts at most the bank's `maximum_consent_validity` (capped at 180 days). `download` refuses
to run once it has expired. Renew by running `authorize` again. Add a calendar reminder for the expiry
date `accounts` shows.

## Optional: 1Password instead of files
`EB_APP_ID` and `EB_PRIVATE_KEY` take the value directly or an `op://` reference, read via `op read`:
```bash
export EB_APP_ID='op://Private/Enable Banking/application_id'
export EB_PRIVATE_KEY='op://Private/Enable Banking/private_key'
```
The key is then held only in memory. `session.json` still lives in `EB_HOME`; it is useless without the key.

## Caveats
- ING may return less history than requested (typically 90 days without fresh SCA); check the CSV range.
- Pending (`PDNG`) transactions can change or disappear; dedupe on `entry_reference`/`transaction_id`
  across captures and prefer `BOOK` rows.
- This is your own financial data: keep `EB_HOME` out of cloud-synced folders unless encrypted.
