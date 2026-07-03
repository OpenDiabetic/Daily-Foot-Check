# Zero-Retention PR Checklist
- [ ] Content is bytes-in-memory end to end (grep open/write/NamedTemporaryFile)
- [ ] Container: read_only + tmpfs + cap_drop + no content volumes
- [ ] Inference server request logging disabled
- [ ] Proxy log format strips bodies/queries/headers
- [ ] Audit fields all allowlisted; additions are hash/enum-only
- [ ] retention_audit.sh covers any new content-touching container
- [ ] /transparency text still accurate after this change
