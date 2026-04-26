# Análise Completa do Sistema SIGAP

## 📋 Visão Geral

**SIGAP** (Sistema de Gestão de Arquivos/Processos) é uma aplicação web Django desenvolvida para gestão documental e fluxo de trabalho em administrações públicas de Angola. O sistema implementa um modelo multi-tenant com isolamento de dados por administração (Ministérios, Governos Provinciais e Administrações Municipais).

---

## 🏗️ Arquitetura do Sistema

### Stack Tecnológico

- **Backend**: Django 4.2.11 (Python 3.12)
- **Banco de Dados**: PostgreSQL (produção) / SQLite (desenvolvimento)
- **Cache/Channel Layer**: Redis
- **Servidor ASGI**: Gunicorn + Uvicorn (9 workers)
- **WebSockets**: Django Channels 4.0.0
- **Frontend**: HTML/CSS/JavaScript (TailwindCSS, Alpine.js)
- **Editor Rich Text**: TinyMCE
- **PDF**: ReportLab + xhtml2pdf
- **Containerização**: Docker + Docker Compose
- **Deploy**: Render.com

### Estrutura de Diretórios

```
SIGAP/
├── SGA/                    # Configurações do projeto Django
│   ├── settings.py         # Configurações principais
│   ├── urls.py            # Rotas principais
│   └── asgi.py            # Configuração ASGI para WebSockets
├── ARQUIVOS/              # App principal
│   ├── models/            # Modelos de dados
│   │   ├── documento.py   # Documentos e anexos
│   │   ├── usuario.py     # Usuários e administrações
│   │   ├── movimentacao.py # Movimentações de documentos
│   │   ├── organizacao.py  # Departamentos e secções
│   │   ├── armazenamento.py # Armazenamento físico
│   │   └── sistema.py      # Notificações e configurações
│   ├── views.py           # Lógica de negócio (1961 linhas)
│   ├── formularios.py     # Formulários Django
│   ├── managers.py        # Custom managers com lógica de isolamento
│   ├── decorators.py      # Decoradores de segurança
│   ├── middleware.py      # Middleware de auditoria
│   ├── consumers.py       # WebSocket consumers
│   └── routing.py         # Rotas WebSocket
├── Paginas/               # Templates HTML
├── media/                 # Arquivos enviados pelos usuários
├── staticfiles/           # Arquivos estáticos compilados
└── requirements.txt       # Dependências Python
```

---

## 🎯 Funcionalidades Principais

### 1. Gestão de Documentos

- **Criação de Documentos**: Protocolo automático (ex: `123/2024`)
- **Tipos de Documentos**: Configuráveis com prazos padrão
- **Anexos**: Múltiplos anexos por documento
- **Digitalização**: Suporte para arquivos digitalizados
- **Níveis de Sigilo**: Público, Restrito, Confidencial
- **Prioridades**: Normal, Urgente, Muito Urgente
- **Status**: Criação → Recebimento → Encaminhamento → Despacho → Aprovado/Reprovado → Arquivado

### 2. Movimentação de Documentos

- **Encaminhamento**: Entre departamentos/secções
- **Confirmação de Recebimento**: Sistema de confirmação obrigatória
- **Despachos**: Registro de decisões
- **Histórico Completo**: Rastreabilidade total
- **Validação de Hierarquia**: Impede movimentações inválidas

### 3. Multi-Tenancy (Isolamento por Administração)

O sistema implementa isolamento rigoroso por **Administração**:

- **Tipos de Administração**:
  - `M`: Ministério
  - `G`: Governo Provincial
  - `A-E`: Administrações Municipais (Tipos A a E)

- **Regras de Comunicação**:
  - Ministério ↔ Governo Provincial: Sempre permitido
  - Governo ↔ Municipal: Apenas mesma província
  - Municipal ↔ Municipal: Apenas mesma província

- **Isolamento de Dados**:
  - Usuários só veem documentos da sua administração
  - Departamentos e secções isolados por administração
  - Validações em múltiplas camadas (models, managers, decorators)

### 4. Hierarquia Organizacional

```
Administração
  └── Departamento (Direção)
      └── Secção (Sub-unidade)
```

- **Departamentos**: Nível de direção
- **Secções**: Sub-unidades dentro de departamentos
- **Isolamento Hierárquico**: Usuários de secção não veem documentos do departamento pai

### 5. Sistema de Permissões e Níveis de Acesso

#### Níveis de Acesso (nivel_acesso)

1. **Gestão**:
   - `admin_sistema`: Administrador de Sistema (acesso total)
   - `ministro`, `secretario_estado`: MAT
   - `governador`, `vice_governador`: Governo Provincial
   - `admin_municipal`, `admin_adjunto`: Administração Municipal

2. **Direção**:
   - `diretor_nacional`: MAT
   - `chefe_departamento`: MAT + Governo
   - `diretor_gabinete`: Governo Provincial
   - `diretor_municipal`, `chefe_seccao`: Administração Municipal

3. **Operacional**:
   - `tecnico`: Todos os tipos

#### Níveis de Sigilo (nivel_sigilo)

- **0 (Técnico)**: Vê apenas documentos atribuídos a ele ou criados por ele (Need-to-Know)
- **1 (Chefia)**: Vê tudo do setor + documentos restritos
- **2 (Direção)**: Vê tudo + documentos confidenciais

### 6. Notificações em Tempo Real

- **WebSockets**: Django Channels com Redis
- **Grupos**: Baseados em usuário, secção e departamento
- **Tipos de Notificação**:
  - Novos documentos encaminhados
  - Confirmações de recebimento
  - Atualizações de pendências
- **Contagem Dinâmica**: Atualização automática de contadores

### 7. Armazenamento Físico

- **Locais Cadastrados**: Estantes, Prateleiras, Dossiês, Caixas, Armários, Pastas
- **Hierarquia**: Locais podem ter pais (ex: Prateleira → Estante)
- **Registro Automático**: Quando documento é recebido ou reencaminhado
- **Histórico**: Rastreamento de movimentações físicas

### 8. Dashboard e Relatórios

- **Estatísticas Dinâmicas**: Baseadas na hierarquia do usuário
- **Métricas**:
  - Pendências (documentos não confirmados)
  - Encaminhados hoje
  - Registrados hoje
  - Documentos na posse
  - Documentos no histórico
  - Arquivo morto

---

## 🔒 Segurança e Auditoria

### Middleware de Auditoria

- **SecurityAuditMiddleware**: Registra tentativas de acesso proibido (403, 404)
- Logs incluem: usuário, administração, path, método HTTP, status code

### Validações de Segurança

1. **Multi-Tenant**: Validação em múltiplas camadas
   - Models: `clean()` methods
   - Managers: Filtros automáticos
   - Decorators: `@requer_mesma_administracao`
   - Views: Verificações explícitas

2. **Hierarquia**: Validação de consistência departamento/secção

3. **Isolamento de Dados**: Usuários só acessam dados da sua administração

### Soft Delete

- Modelos principais implementam `SoftDeleteModel`
- Exclusão lógica (não física)
- Rastreamento de data de exclusão

---

## 📊 Modelos de Dados Principais

### Documento

```python
- numero_protocolo: CharField (único, auto-gerado)
- titulo: CharField
- conteudo: TextField
- tipo_documento: ForeignKey(TipoDocumento)
- arquivo: FileField
- arquivo_digitalizado: FileField
- status: CharField (choices)
- prioridade: CharField
- niveis: CharField (Público/Restrito/Confidencial)
- departamento_origem: ForeignKey(Departamento)
- departamento_atual: ForeignKey(Departamento)
- seccao_atual: ForeignKey(Seccoes, nullable)
- administracao: ForeignKey(Administracao) # CRÍTICO para isolamento
- criado_por: ForeignKey(CustomUser)
- responsavel_atual: ForeignKey(CustomUser, nullable)
- data_criacao: DateTimeField
- data_prazo: DateTimeField
- data_conclusao: DateTimeField
```

### CustomUser

```python
- nivel_acesso: CharField (choices)
- nivel_sigilo: IntegerField (0-2)
- departamento: ForeignKey(Departamento, nullable)
- seccao: ForeignKey(Seccoes, nullable)
- administracao: ForeignKey(Administracao) # CRÍTICO para isolamento
- telefone: CharField
```

### MovimentacaoDocumento

```python
- documento: ForeignKey(Documento)
- tipo_movimentacao: CharField
- departamento_origem: ForeignKey(Departamento, nullable)
- seccao_origem: ForeignKey(Seccoes, nullable)
- departamento_destino: ForeignKey(Departamento, nullable)
- seccao_destino: ForeignKey(Seccoes, nullable)
- usuario: ForeignKey(CustomUser)
- observacoes: TextField
- despacho: TextField
- confirmado_recebimento: BooleanField
- data_confirmacao: DateTimeField
```

### Administracao

```python
- nome: CharField
- tipo_municipio: CharField (M/G/A-E)
- provincia: CharField
```

### Departamento

```python
- nome: CharField
- codigo: CharField
- administracao: ForeignKey(Administracao) # CRÍTICO
- tipo_municipio: CharField
- responsavel: ForeignKey(CustomUser, nullable)
```

### Seccoes

```python
- departamento: ForeignKey(Departamento)
- nome: CharField
- codigo: CharField
- responsavel: ForeignKey(CustomUser, nullable)
- administracao: Property (herda do departamento)
```

---

## 🔄 Fluxos de Trabalho

### Fluxo de Criação de Documento

1. Usuário cria documento → `DocumentoForm`
2. Sistema gera protocolo automático (`{pk}/{ano}`)
3. Define `departamento_origem` e `seccao_atual` baseado no usuário
4. Cria primeira movimentação (`tipo='criacao'`)
5. Notifica usuários do setor via WebSocket

### Fluxo de Encaminhamento

1. Usuário seleciona documento → `EncaminharDocumentoForm`
2. Validações:
   - Mesma administração OU comunicação permitida
   - Hierarquia válida
   - Permissões do usuário
3. Cria `MovimentacaoDocumento` (`tipo='encaminhamento'`)
4. Atualiza `departamento_atual` e `seccao_atual` do documento
5. Notifica destino via WebSocket
6. Registra armazenamento físico (se aplicável)

### Fluxo de Confirmação de Recebimento

1. Usuário recebe notificação de pendência
2. Acessa documento → `confirmar_recebimento`
3. Marca `confirmado_recebimento=True`
4. Atualiza contadores de pendências via WebSocket
5. Remove da lista de pendências

### Fluxo de Despacho

1. Usuário com permissão cria despacho → `DespachoForm`
2. Gera PDF do despacho (`gerar_pdf_despacho`)
3. Cria movimentação (`tipo='despacho'`)
4. Atualiza status do documento
5. Notifica interessados

---

## 🚀 Deploy e Infraestrutura

### Docker Compose

```yaml
services:
  web:        # Django + Gunicorn + Uvicorn (9 workers)
  db:         # PostgreSQL 16
  redis:      # Redis 7 (Channel Layer)
  nginx:      # Reverse proxy
```

### Configurações de Produção

- **Workers**: 9 Uvicorn workers
- **Timeout**: 120 segundos
- **Keep-Alive**: 5 segundos
- **Static Files**: WhiteNoise com compressão Brotli
- **Database**: PostgreSQL com connection pooling
- **Redis**: Channel Layer para WebSockets

### Variáveis de Ambiente

- `DEBUG`: False (produção)
- `DATABASE_URL`: URL PostgreSQL
- `REDIS_URL`: URL Redis
- `SECRET_KEY`: Chave secreta Django
- `ALLOWED_HOSTS`: Hosts permitidos
- `CSRF_TRUSTED_ORIGINS`: Origens confiáveis

---

## ⚠️ Pontos de Atenção e Melhorias Sugeridas

### 1. Segurança

- ✅ **Bom**: Isolamento multi-tenant implementado
- ⚠️ **Atenção**: `DEBUG=True` em produção (linha 23 de settings.py)
- ⚠️ **Atenção**: `SECRET_KEY` com valor padrão inseguro
- 💡 **Sugestão**: Usar variáveis de ambiente para todos os secrets

### 2. Performance

- ✅ **Bom**: `select_related` nos managers
- ⚠️ **Atenção**: Views com queries complexas podem ser otimizadas
- 💡 **Sugestão**: Implementar cache para estatísticas do dashboard
- 💡 **Sugestão**: Paginação em todas as listagens

### 3. Código

- ⚠️ **Atenção**: `views.py` muito grande (1961 linhas)
- 💡 **Sugestão**: Refatorar em múltiplos arquivos ou class-based views
- ⚠️ **Atenção**: Campos `null=True` temporários em modelos críticos
- 💡 **Sugestão**: Migração para tornar campos obrigatórios

### 4. Testes

- ⚠️ **Atenção**: Poucos testes automatizados
- 💡 **Sugestão**: Expandir cobertura de testes
- ✅ **Bom**: Testes existentes para isolamento e fluxo hierárquico

### 5. Documentação

- ⚠️ **Atenção**: Falta documentação de API
- 💡 **Sugestão**: Adicionar docstrings mais detalhadas
- 💡 **Sugestão**: Criar guia de usuário

### 6. Banco de Dados

- ⚠️ **Atenção**: Múltiplos arquivos SQLite no repositório
- 💡 **Sugestão**: Adicionar ao `.gitignore`
- 💡 **Sugestão**: Migrar completamente para PostgreSQL

---

## 📈 Métricas e Estatísticas

### Complexidade do Código

- **Total de Modelos**: 12+
- **Total de Views**: 30+
- **Total de Formulários**: 12+
- **Linhas de Código**: ~10.000+ (estimativa)
- **Migrations**: 35 arquivos

### Funcionalidades Implementadas

- ✅ Gestão completa de documentos
- ✅ Sistema de movimentação
- ✅ Multi-tenancy
- ✅ Notificações em tempo real
- ✅ Armazenamento físico
- ✅ Dashboard dinâmico
- ✅ Sistema de permissões hierárquico
- ✅ Soft delete
- ✅ Auditoria de segurança

---

## 🎓 Conclusão

O **SIGAP** é um sistema robusto e bem estruturado para gestão documental em administrações públicas. Implementa conceitos avançados como multi-tenancy, isolamento hierárquico, notificações em tempo real e controle de acesso baseado em sigilo.

### Pontos Fortes

1. Arquitetura multi-tenant bem implementada
2. Isolamento de dados rigoroso
3. Sistema de permissões granular
4. Notificações em tempo real funcionais
5. Rastreabilidade completa de documentos

### Áreas de Melhoria

1. Refatoração de código (views.py muito grande)
2. Melhorar segurança (DEBUG, SECRET_KEY)
3. Expandir testes automatizados
4. Otimização de queries
5. Documentação mais completa

---

**Data da Análise**: 2025-01-27
**Versão Analisada**: Baseada no código atual do repositório
