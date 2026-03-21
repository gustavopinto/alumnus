"""Domínios de e-mail públicos/gratuitos — não aceitos para novo cadastro sem pesquisador vinculado."""

from __future__ import annotations

# Lista extensível: provedores pessoais comuns (Brasil e internacional).
_PUBLIC_EMAIL_DOMAINS = frozenset({
    "gmail.com",
    "googlemail.com",
    "hotmail.com",
    "hotmail.com.br",
    "hotmail.co.uk",
    "hotmail.fr",
    "outlook.com",
    "outlook.com.br",
    "live.com",
    "live.com.br",
    "msn.com",
    "yahoo.com",
    "yahoo.com.br",
    "yahoo.co.uk",
    "yahoo.fr",
    "ymail.com",
    "rocketmail.com",
    "icloud.com",
    "me.com",
    "mac.com",
    "protonmail.com",
    "proton.me",
    "pm.me",
    "tutanota.com",
    "tuta.io",
    "mail.com",
    "gmx.com",
    "gmx.net",
    "gmx.de",
    "aol.com",
    "zoho.com",
    "hey.com",
    "fastmail.com",
    "duck.com",
    "yandex.com",
    "yandex.ru",
    # Brasil — provedores de acesso pessoal
    "uol.com.br",
    "bol.com.br",
    "terra.com.br",
    "ig.com.br",
    "r7.com",
    "globo.com",
    "oi.com.br",
})


def extract_domain(email: str) -> str:
    s = (email or "").strip().lower()
    if "@" not in s:
        return ""
    return s.rsplit("@", 1)[-1]


def is_public_email_domain(email: str) -> bool:
    """True se o domínio for de provedor público/gratuito típico."""
    d = extract_domain(email)
    return bool(d) and d in _PUBLIC_EMAIL_DOMAINS


INSTITUTIONAL_EMAIL_HELP_PT = (
    "Use um e-mail institucional da sua universidade "
    "(ex.: @universidade.edu.br, @usp.br). "
    "E-mails públicos (Gmail, Hotmail, Outlook, UOL etc.) não são aceitos para cadastro."
)
