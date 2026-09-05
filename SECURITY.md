# Security policy

Never open an issue or commit containing an API key, SSH key, access token,
signed download URL, private dataset sample, or unredacted provider response.

Credentials must be supplied through environment variables named by the selected
configuration. Local secret files live outside the Git working tree or under the
ignored `secrets/` directory and should be readable only by their owner.

If a credential is committed, revoke it immediately, rotate it at the provider,
and remove it from Git history. Deleting it in a later commit is not sufficient.
