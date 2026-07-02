# 03 — Aplicar Decisões — Engenharia (RFC-003)


> Especificação técnica da etapa **Aplicar Decisões**.
>
> Este documento define arquitetura, contratos, persistência, concorrência, jobs,
> auditoria, observabilidade e critérios técnicos de implementação.


# 1. Contexto


A etapa recebe decisões aprovadas em **Revisar Pendências** e persiste os
`mangaupdates_id` no catálogo principal de forma segura, auditável e resiliente.


# 2. Objetivo Técnico


- Validar o lote.
- Persistir IDs confirmados.
- Registrar auditoria.
- Permitir falha parcial.
- Disponibilizar progresso do processamento.


# 3. Arquitetura


```text
Frontend
   │
POST /apply
   │
API
   │
Validação
   │
Job Queue
   │
Worker
   │
Transaction
   │
Audit Log
   │
Commit
```


# 4. Máquina de Estados


```text
READY
 ↓
VALIDATING
 ↓
QUEUED
 ↓
RUNNING
 ↓
COMPLETED
 ↘
 FAILED
```


# 5. Contratos REST


| Método | Endpoint | Finalidade |
|---|---|---|
| GET | /api/mangaupdates/decisions/ready | Buscar lote |
| POST | /api/mangaupdates/decisions/validate | Validar |
| POST | /api/mangaupdates/decisions/apply | Iniciar job |
| GET | /api/jobs/{jobId} | Consultar progresso |


# 6. DTOs


```ts
export interface ApplyRequest{
 queueIds:string[];
 dryRun?:boolean;
}
export interface ApplyResponse{
 jobId:string;
 accepted:number;
 blocked:number;
}
```


# 7. Persistência


A gravação é transacional por item.

Falhas não cancelam o lote inteiro.

Cada item registra:
- início;
- fim;
- duração;
- resultado.


# 8. SQL


```sql
UPDATE mangas
SET mangaupdates_id = :id,
    updated_at = NOW()
WHERE id = :manga_id;
```


# 9. Concorrência


- Lock otimista por registro.
- Revalidar antes do commit.
- Evitar dupla aplicação do mesmo queueId.


# 10. Auditoria


Registrar:

- executionId
- queueId
- mangaId
- oldValue
- newValue
- user
- timestamp
- duration
- result


# 11. Observabilidade


Logs estruturados.

Métricas:
- tempo médio;
- itens/minuto;
- taxa de falhas;
- retries.


# 12. Recuperação


- Retry somente dos bloqueados.
- Job idempotente.
- Reprocessamento seguro.


# 13. Edge Cases


- timeout;
- stale data;
- duplicidade;
- perda de conexão;
- worker interrompido;
- rollback parcial.


# 14. Testes


Cobrir:

- happy path;
- dry-run;
- duplicate;
- timeout;
- rollback;
- concorrência;
- falha parcial.


# Contrato Técnico 1


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 2


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 3


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 4


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 5


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 6


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 7


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 8


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 9


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 10


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 11


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 12


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 13


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 14


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 15


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 16


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 17


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 18


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 19


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 20


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 21


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 22


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 23


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 24


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 25


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 26


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 27


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 28


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 29


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 30


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 31


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 32


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 33


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 34


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 35


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 36


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 37


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 38


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 39


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 40


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 41


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 42


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 43


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 44


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# Contrato Técnico 45


## Objetivo

Definir comportamento obrigatório do backend.

### Requisitos

- operações idempotentes;
- validação antes da persistência;
- logs estruturados;
- mensagens de erro determinísticas;
- sem dependência da interface.

### Critérios

A implementação deve manter compatibilidade com os contratos REST,
DTOs e máquina de estados definidos neste documento.


# 15. Critérios de Aceite Técnico


- Nenhuma gravação sem validação.
- Auditoria obrigatória.
- Falha parcial suportada.
- API idempotente.
- Jobs observáveis.
- Cobertura de testes automatizados.

