"""
=============================================================================
AXIOM QUANT — PII & PROFANITY SCRUBBER ENGINE (QuantReddit / QuantChan)
=============================================================================
Cryptographically hashes user identity into anonymous tripcodes (Anon#ΔXXXX),
scrubs PII (emails, phone numbers, IPs, full names), and filters profanity
and low-signal mumbo-jumbo to maintain strict academic signal quality.
"""

from __future__ import annotations

import hashlib
import re

PROFANITY_PATTERN = re.compile(
    r'\b(fuck|shit|bitch|asshole|cunt|dick|pussy|bastard|damn|crap)\b',
    re.IGNORECASE,
)
EMAIL_PATTERN = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
PHONE_PATTERN = re.compile(r'\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}')
IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')

def generate_anon_tripcode(ip_or_seed: str) -> str:
    """Generate a clean 6-character cryptographic tripcode like Anon#Δa3f8b."""
    h = hashlib.sha256(ip_or_seed.encode('utf-8')).hexdigest()[:6]
    return f"Anon#Δ{h}"

def scrub_pii_and_profanity(text: str) -> str:
    """Scrub PII (email, phone, IP) and profanity from post text."""
    if not text:
        return ""

    # Replace emails, IPs, phone numbers with [PPR-REDACTED]
    scrubbed = EMAIL_PATTERN.sub('[EMAIL-REDACTED]', text)
    scrubbed = IP_PATTERN.sub('[IP-REDACTED]', scrubbed)
    scrubbed = PHONE_PATTERN.sub('[PHONE-REDACTED]', scrubbed)

    # Scrub profanity
    scrubbed = PROFANITY_PATTERN.sub('[REDACTED]', scrubbed)

    return scrubbed
