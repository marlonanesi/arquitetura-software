FROM postgres:16-alpine

# Pastas de arquivamento de WAL e de backup base, com o dono certo para os volumes herdarem.
RUN mkdir -p /arquivo /backups && chown postgres:postgres /arquivo /backups
