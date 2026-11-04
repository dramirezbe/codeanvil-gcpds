# File formats

## snapshot.json (source-snapshot/1)
`entries[]: {path, bytes, sha256}` sorted by path; `manifest_digest` = SHA-256 of canonical JSON of `entries`.

## ports.json
`ports[]: {id, interface: "pkg.mod:Class", binding: "pkg.mod:Impl", required: bool, scope: str}`

## controls.json
`controls[]: {id, title, description, params: {name: {type, value[, enum]}}, check: {operator, param}}`
Types: string, integer, number, boolean, enum, path, sha256, list.
Operators: eq ne lt lte gt gte in not_in matches_enum sha256_equals bytes_equals exists bound.

## custody.jsonl (one JSON object per line)
seq, ts_utc, actor, role, action, doc_path, doc_sha256, doc_bytes, prev_doc_sha256, detail,
observed_os_user, host, prev_hash, key_id, entry_hash, signature.
entry_hash = SHA-256(canonical JSON of entry without entry_hash/signature); signature = HMAC-SHA256(key, entry_hash).
