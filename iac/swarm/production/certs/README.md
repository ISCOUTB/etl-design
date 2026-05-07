# Certificates

This directory requires two files to be present before deploying: `fullchain.crt` and `domain.key`.

## File descriptions

**`fullchain.crt`** — The full certificate chain, formed by concatenating the server certificate and the CA certificate in the following order:

```text
-----BEGIN CERTIFICATE-----
<SERVER CERTIFICATE>
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
<CA CERTIFICATE>
-----END CERTIFICATE-----
```

**`domain.key`** — The private key associated with the certificate. This file must be kept secret and should never be committed to version control.

## Obtaining these files

### From a certificate authority (e.g. name.com)

Most CAs require you to submit a CSR (Certificate Signing Request), which you can generate locally along with the private key:

```console
openssl req -newkey rsa:2048 -nodes -keyout domain.key \
  -out domain.csr \
  -subj "/CN=${DOMAIN}" \
  -addext "subjectAltName=DNS:${DOMAIN},DNS:*.${DOMAIN}"
```

Submit the resulting `domain.csr` to the CA. They will provide a server certificate and a CA certificate in return. Concatenate them as shown above to produce `fullchain.crt`. The `domain.key` generated here is the private key to use.

### Self-signed certificate (for local or non-production use)

A self-signed certificate can be generated directly without involving a CA. Browsers will display a security warning when using it, but it is otherwise functional:

```console
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout domain.key -out fullchain.crt \
  -days 365 -subj "/CN=${DOMAIN}" \
  -addext "subjectAltName=DNS:${DOMAIN},DNS:*.${DOMAIN}"
```

> **Note:** The `subjectAltName` extension is required for modern browsers and TLS clients to accept the certificate. A CN-only certificate will be rejected.
