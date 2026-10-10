#!/usr/bin/env python3
"""Read-only Enable Banking (AIS) client for downloading personal ING Bank Śląski transactions.

Subcommands:
  keygen      generate RSA signing key + self-signed certificate to upload in the control panel
  banks       list ASPSPs for a country (sanity check that the app works)
  authorize   create an API session: POST /auth -> bank login -> paste redirect URL -> POST /sessions
  accounts    show accounts and consent expiry of the stored session
  download    download transactions for --month / --date / --date-from + --date-to

Secrets (resolved in this order, values starting with op:// are read via the 1Password CLI):
  EB_APP_ID        application ID            else $EB_HOME/app_id
  EB_PRIVATE_KEY   PEM text or op:// ref     else $EB_HOME/private.pem
  EB_HOME          state dir (default ~/.enable-banking), holds session.json and captures/
"""
import argparse
import calendar
import csv
import datetime as dt
import json
import os
import subprocess
import sys
import time
import uuid
import webbrowser
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import jwt
import requests

API = "https://api.enablebanking.com"
EB_HOME = Path(os.environ.get("EB_HOME", Path.home() / ".enable-banking"))
DEFAULT_BANK = "ING"
DEFAULT_COUNTRY = "PL"
DEFAULT_REDIRECT = "https://localhost:8766/callback"
MAX_CONSENT_DAYS = 180


# ---------- secrets / state ----------

def _resolve(value: str) -> str:
    if value.startswith("op://"):
        return subprocess.run(["op", "read", value], check=True, capture_output=True, text=True).stdout.strip()
    return value


def _secret(env: str, file_name: str) -> str:
    if os.environ.get(env):
        return _resolve(os.environ[env])
    path = EB_HOME / file_name
    if not path.exists():
        sys.exit(f"Missing {env} and {path}. Run `keygen` / save the application ID first (see banking/README.md).")
    return path.read_text().strip()


def _write_private(path: Path, data: str) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(data)


def _load_session() -> dict:
    path = EB_HOME / "session.json"
    if not path.exists():
        sys.exit(f"No session at {path}. Run `authorize` first.")
    return json.loads(path.read_text())


# ---------- API ----------

class Client:
    def __init__(self):
        app_id = _secret("EB_APP_ID", "app_id")
        key = _secret("EB_PRIVATE_KEY", "private.pem")
        now = int(time.time())
        token = jwt.encode(
            {"iss": "enablebanking.com", "aud": "api.enablebanking.com", "iat": now, "exp": now + 3600},
            key,
            algorithm="RS256",
            headers={"kid": app_id},
        )
        self.s = requests.Session()
        self.s.headers["Authorization"] = f"Bearer {token}"

    def _call(self, method: str, path: str, **kw) -> dict:
        r = self.s.request(method, API + path, timeout=60, **kw)
        if not r.ok:
            raise RuntimeError(f"{method} {path} -> HTTP {r.status_code}: {r.text[:500]}")
        return r.json()

    def get(self, path, **params):
        return self._call("GET", path, params={k: v for k, v in params.items() if v is not None})

    def post(self, path, body):
        return self._call("POST", path, json=body)


# ---------- commands ----------

def cmd_keygen(args):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID

    key_path, crt_path = EB_HOME / "private.pem", EB_HOME / "public.crt"
    if key_path.exists() and not args.force:
        sys.exit(f"{key_path} exists; use --force to overwrite (this invalidates the registered app).")
    key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, args.cn)])
    now = dt.datetime.now(dt.timezone.utc)
    cert = (
        x509.CertificateBuilder().subject_name(name).issuer_name(name)
        .public_key(key.public_key()).serial_number(x509.random_serial_number())
        .not_valid_before(now).not_valid_after(now + dt.timedelta(days=3650))
        .sign(key, hashes.SHA256())
    )
    _write_private(key_path, key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode())
    crt_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    print(f"Private key : {key_path}  (keep secret; store in your password manager)")
    print(f"Certificate : {crt_path}  (upload this during application registration)")


def cmd_banks(args):
    for a in Client().get("/aspsps", country=args.country, psu_type="personal")["aspsps"]:
        days = (a.get("maximum_consent_validity") or 0) // 86400
        print(f"{a['name']:<40} max consent {days} days")


def cmd_authorize(args):
    c = Client()
    aspsps = c.get("/aspsps", country=args.country, psu_type="personal")["aspsps"]
    want = args.bank.lower()
    match = [a for a in aspsps if a["name"].lower() == want] or [a for a in aspsps if want in a["name"].lower()]
    if len(match) != 1:
        names = ", ".join(a["name"] for a in (match or aspsps))
        sys.exit(f"Bank {args.bank!r} is not a unique match in {args.country}. Use --bank with one of: {names}")
    aspsp = match[0]
    max_days = min(MAX_CONSENT_DAYS, (aspsp.get("maximum_consent_validity") or 90 * 86400) // 86400)
    days = min(args.days or max_days, max_days)
    valid_until = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days)).isoformat(timespec="seconds")
    state = str(uuid.uuid4())
    auth = c.post("/auth", {
        "access": {"valid_until": valid_until},
        "aspsp": {"name": aspsp["name"], "country": args.country},
        "state": state,
        "redirect_url": args.redirect_url,
        "psu_type": "personal",
    })
    print(f"Consent requested until {valid_until} ({days} days).\n\nOpen this URL and approve access in ING:\n\n  {auth['url']}\n")
    try:
        webbrowser.open(auth["url"])
    except Exception:
        pass
    print("After approval the browser is sent to the callback URL. The page will NOT load - that is expected.")
    redirected = input("Paste the full URL from the address bar: ").strip()
    q = parse_qs(urlparse(redirected).query)
    if "error" in q:
        sys.exit(f"Bank returned error: {q['error'][0]} {q.get('error_description', [''])[0]}")
    if q.get("state", [None])[0] != state:
        sys.exit("State mismatch - refusing to exchange the code (stale or foreign callback URL).")
    code = q.get("code", [None])[0]
    if not code:
        sys.exit("No `code` parameter in the URL.")
    sess = c.post("/sessions", {"code": code})
    _write_private(EB_HOME / "session.json", json.dumps(sess, indent=2))
    print(f"\nSession {sess['session_id']} saved to {EB_HOME / 'session.json'}")
    _print_accounts(sess)


def _accounts(sess: dict) -> list[dict]:
    return [a if isinstance(a, dict) else {"uid": a} for a in sess.get("accounts", [])]


def _iban(a: dict) -> str:
    return (a.get("account_id") or {}).get("iban") or a.get("uid", "")


def _print_accounts(sess):
    print(f"Consent valid until: {sess.get('access', {}).get('valid_until')}")
    for a in _accounts(sess):
        print(f"  {a['uid']}  {_iban(a):<30} {a.get('currency', ''):<4} {a.get('name') or a.get('product') or ''}")


def cmd_accounts(args):
    sess = _load_session()
    live = Client().get(f"/sessions/{sess['session_id']}")
    print(f"Session status: {live.get('status')}")
    _print_accounts(sess)


def _date_range(args) -> tuple[dt.date, dt.date, str]:
    if args.month:
        y, m = map(int, args.month.split("-"))
        return dt.date(y, m, 1), dt.date(y, m, calendar.monthrange(y, m)[1]), args.month
    if args.date:
        d = dt.date.fromisoformat(args.date)
        return d, d, args.date
    if args.date_from and args.date_to:
        f, t = dt.date.fromisoformat(args.date_from), dt.date.fromisoformat(args.date_to)
        if f > t:
            sys.exit("--date-from is after --date-to")
        return f, t, f"{f}_{t}"
    sys.exit("Use --month YYYY-MM, --date YYYY-MM-DD, or --date-from + --date-to.")


def _amount(m):
    return (m or {}).get("amount", ""), (m or {}).get("currency", "")


CSV_FIELDS = [
    "account_uid", "account_iban", "booking_date", "value_date", "transaction_date", "status",
    "credit_debit_indicator", "amount", "currency", "signed_amount", "counterparty_name", "counterparty_iban",
    "creditor_name", "creditor_iban", "debtor_name", "debtor_iban", "description", "note",
    "balance_after", "balance_after_currency", "merchant_category_code", "bank_transaction_code",
    "entry_reference", "transaction_id", "reference_number", "raw_json",
]


def _row(acc: dict, t: dict) -> dict:
    amount, currency = _amount(t.get("transaction_amount"))
    debit = t.get("credit_debit_indicator") == "DBIT"
    cred, deb = t.get("creditor") or {}, t.get("debtor") or {}
    cred_acc, deb_acc = t.get("creditor_account") or {}, t.get("debtor_account") or {}
    cp, cp_acc = (cred, cred_acc) if debit else (deb, deb_acc)
    bal_amount, bal_currency = _amount((t.get("balance_after_transaction") or {}).get("balance_amount"))
    btc = t.get("bank_transaction_code") or {}
    return {
        "account_uid": acc["uid"], "account_iban": _iban(acc),
        "booking_date": t.get("booking_date") or "", "value_date": t.get("value_date") or "",
        "transaction_date": t.get("transaction_date") or "", "status": t.get("status") or "",
        "credit_debit_indicator": t.get("credit_debit_indicator") or "",
        "amount": amount, "currency": currency,
        "signed_amount": (f"-{amount}" if debit and amount else amount),
        "counterparty_name": cp.get("name") or "", "counterparty_iban": cp_acc.get("iban") or "",
        "creditor_name": cred.get("name") or "", "creditor_iban": cred_acc.get("iban") or "",
        "debtor_name": deb.get("name") or "", "debtor_iban": deb_acc.get("iban") or "",
        "description": " | ".join(t.get("remittance_information") or []), "note": t.get("note") or "",
        "balance_after": bal_amount, "balance_after_currency": bal_currency,
        "merchant_category_code": t.get("merchant_category_code") or "",
        "bank_transaction_code": btc.get("description") or btc.get("code") or "",
        "entry_reference": t.get("entry_reference") or "", "transaction_id": t.get("transaction_id") or "",
        "reference_number": t.get("reference_number") or "",
        "raw_json": json.dumps(t, ensure_ascii=False, sort_keys=True),
    }


def cmd_download(args):
    date_from, date_to, label = _date_range(args)
    sess = _load_session()
    valid_until = sess.get("access", {}).get("valid_until")
    if valid_until and dt.datetime.fromisoformat(valid_until.replace("Z", "+00:00")) < dt.datetime.now(dt.timezone.utc):
        sys.exit(f"Consent expired at {valid_until}. Run `authorize` again.")
    c = Client()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(args.out or EB_HOME / "captures") / f"{label}_{stamp}"
    (out / "raw").mkdir(parents=True, exist_ok=False)
    os.chmod(out, 0o700)

    manifest = {
        "session_id": sess["session_id"], "date_from": str(date_from), "date_to": str(date_to),
        "started_at": stamp, "accounts": [], "complete": False,
    }
    rows = []
    for acc in _accounts(sess):
        uid = acc["uid"]
        entry = {"uid": uid, "iban": _iban(acc), "pages": 0, "transactions": 0, "complete": False, "error": None}
        manifest["accounts"].append(entry)
        key, seen = None, set()
        try:
            while True:
                page = c.get(f"/accounts/{uid}/transactions", date_from=str(date_from),
                             date_to=str(date_to), continuation_key=key)
                entry["pages"] += 1
                (out / "raw" / f"{uid}_p{entry['pages']:03d}.json").write_text(
                    json.dumps(page, indent=2, ensure_ascii=False))
                txs = page.get("transactions") or []
                entry["transactions"] += len(txs)
                rows += [_row(acc, t) for t in txs]
                key = page.get("continuation_key")
                if not key:
                    break
                if key in seen:
                    raise RuntimeError("continuation_key repeated; aborting to avoid an endless loop")
                seen.add(key)
            entry["complete"] = True
        except Exception as e:  # keep going for other accounts, but the capture is marked incomplete
            entry["error"] = str(e)
        print(f"{entry['iban']:<30} pages={entry['pages']:<3} tx={entry['transactions']:<5} "
              f"{'OK' if entry['complete'] else 'FAILED: ' + entry['error']}")

    rows.sort(key=lambda r: (r["booking_date"] or r["value_date"] or r["transaction_date"], r["account_iban"]))
    with open(out / "transactions.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(rows)
    manifest["complete"] = bool(manifest["accounts"]) and all(a["complete"] for a in manifest["accounts"])
    manifest["transactions"] = len(rows)
    manifest["finished_at"] = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\n{'COMPLETE' if manifest['complete'] else 'INCOMPLETE'}: {len(rows)} transactions -> {out}")
    sys.exit(0 if manifest["complete"] else 2)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    k = sub.add_parser("keygen")
    k.add_argument("--cn", default="household-budgeting")
    k.add_argument("--force", action="store_true")
    k.set_defaults(fn=cmd_keygen)

    b = sub.add_parser("banks")
    b.add_argument("--country", default=DEFAULT_COUNTRY)
    b.set_defaults(fn=cmd_banks)

    a = sub.add_parser("authorize")
    a.add_argument("--bank", default=DEFAULT_BANK)
    a.add_argument("--country", default=DEFAULT_COUNTRY)
    a.add_argument("--redirect-url", default=DEFAULT_REDIRECT)
    a.add_argument("--days", type=int, help=f"consent length, capped by the bank and {MAX_CONSENT_DAYS}")
    a.set_defaults(fn=cmd_authorize)

    sub.add_parser("accounts").set_defaults(fn=cmd_accounts)

    d = sub.add_parser("download")
    d.add_argument("--month")
    d.add_argument("--date")
    d.add_argument("--date-from")
    d.add_argument("--date-to")
    d.add_argument("--out", help="capture root (default $EB_HOME/captures)")
    d.set_defaults(fn=cmd_download)

    args = p.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
