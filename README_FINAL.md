# WhatsApp Medical Bot - Sistema Completo

Sistema completo de bot WhatsApp para campanhas médicas com interface administrativa web.

## 🚀 Funcionalidades Implementadas

### ✅ Bot WhatsApp Original
- Sistema u-ETG com sorteio automático
- Lembretes médicos personalizados
- Questionários PHQ-9, GAD-7
- Integração com iClinic

### ✅ Sistema Admin PostgreSQL + Interface Web
- **PostgreSQL** com migrations Alembic
- **Interface Admin** responsiva (Tailwind + HTMX)
- **CRUD de Campanhas** completo
- **Scheduler Worker** automático
- **API REST** protegida por token

## 📋 Variáveis de Ambiente Necessárias

### WhatsApp (Obrigatórias)
```bash
WHATSAPP_ACCESS_TOKEN=EAANTZCXB0csgBPft9y6ZBIdeTVM5PVLr2ZBZAlTGd49ezcAklZCF4DDZC6r6NQ4nrDREkNnC6iEebI7YxciceIMF9BD9Cwp8OqVpBYxeZB2gAZADsVQZCsDbDZAlaPZC3iByj0ZAn2eaSrmjPaQPqZBX6UJZAK6Hd8MuXGoKVrLFPooE7so4G1w2wYNaxJYn1SgQ6RnwZDZD
WHATSAPP_PHONE_NUMBER_ID=797803706754193
APP_SECRET=b6d92b5c5f3db984e02e4dd25c676e1c
```

### Admin Interface (Obrigatória)
```bash
ADMIN_UI_TOKEN=guilherme_admin_2025_!
```

### Sistema (Opcionais)
```bash
ADMIN_PHONE_NUMBER=5514997799022
TZ=America/Sao_Paulo
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

### u-ETG (Opcionais)
```bash
UETG_PATIENT_PHONE=5514997799022
UETG_PATIENT_NAME=Guilherme
```

## 🛠️ Deploy no Railway

### 1. Configurar Variáveis
No Railway → Seu Projeto → Variables:
```
WHATSAPP_ACCESS_TOKEN = (seu token)
WHATSAPP_PHONE_NUMBER_ID = 797803706754193
APP_SECRET = b6d92b5c5f3db984e02e4dd25c676e1c
ADMIN_UI_TOKEN = guilherme_admin_2025_!
ADMIN_PHONE_NUMBER = 5514997799022
TZ = America/Sao_Paulo
```

### 2. Adicionar PostgreSQL
Railway → Add Service → PostgreSQL
(DATABASE_URL será configurado automaticamente)

### 3. Deploy
- Push do código para GitHub
- Railway detecta automaticamente
- Migrations executam na inicialização

## 🎯 Como Usar

### Acessar Interface Admin
1. **URL:** `https://seu-app.up.railway.app/admin`
2. **Token:** Use o valor de `ADMIN_UI_TOKEN`
3. **Login:** Insira o token na tela de login

### Criar Campanha de Teste
1. **Acesse:** `/admin/campaigns/new`
2. **Configure:**
   - Nome: "Teste u-ETG"
   - Template: `uetg_paciente_agenda_ptbr`
   - Frequência: "once" (única)
   - Início: Agora + 2 minutos
   - Horário: Atual
   - Destinatário: Seu número

### Testar Template Rápido
1. **Dashboard:** Clique em "Testar Template"
2. **Ou API:** `POST /admin/api/test-template`
   ```bash
   curl -X POST https://seu-app.up.railway.app/admin/api/test-template \
     -H "X-Admin-Token: guilherme_admin_2025_!"
   ```

## 📊 Endpoints da API

### Autenticação
Todas as APIs requerem header:
```
X-Admin-Token: guilherme_admin_2025_!
```

### Principais Endpoints
```bash
# Estatísticas
GET /admin/api/stats
GET /admin/api/dashboard/stats

# Campanhas
GET /admin/api/campaigns
POST /admin/api/campaigns
POST /admin/api/campaigns/{id}/pause
POST /admin/api/campaigns/{id}/resume
POST /admin/api/campaigns/{id}/test

# Testes
POST /admin/api/test-template
```

## 🔧 Exemplo de Campanha via API

```bash
curl -X POST https://seu-app.up.railway.app/admin/api/campaigns \
  -H "Content-Type: application/json" \
  -H "X-Admin-Token: guilherme_admin_2025_!" \
  -d '{
    "name": "Lembrete u-ETG Semanal",
    "template_name": "uetg_paciente_agenda_ptbr",
    "lang_code": "pt_BR",
    "params_mode": "fixed",
    "fixed_params": {
      "1": "Guilherme",
      "2": "19/09/2025"
    },
    "frequency": "weekly",
    "days_of_week": [2, 5],
    "send_time": "08:00",
    "start_at": "2025-01-18T00:00:00Z",
    "recipients": ["5514997799022"]
  }'
```

## 📅 Tipos de Frequência

### Once (Única)
```json
{
  "frequency": "once",
  "start_at": "2025-01-18T14:30:00Z",
  "send_time": "14:30"
}
```

### Daily (Diária)
```json
{
  "frequency": "daily",
  "send_time": "08:00",
  "start_at": "2025-01-18T00:00:00Z",
  "end_at": "2025-12-31T23:59:59Z"
}
```

### Weekly (Semanal)
```json
{
  "frequency": "weekly",
  "days_of_week": [1, 3, 5],
  "send_time": "09:00"
}
```

### Monthly (Mensal)
```json
{
  "frequency": "monthly",
  "day_of_month": 15,
  "send_time": "10:00"
}
```

### Cron (Personalizada)
```json
{
  "frequency": "cron",
  "cron_expr": "0 0 8 * * 1-5",
  "send_time": "08:00"
}
```

## 🧪 Testes de Funcionamento

### 1. Health Check
```bash
curl https://seu-app.up.railway.app/health
```

### 2. Teste de Template
```bash
curl -X POST https://seu-app.up.railway.app/admin/api/test-template \
  -H "X-Admin-Token: guilherme_admin_2025_!"
```

### 3. Campanha Imediata
1. Crie campanha "once" para daqui 2 minutos
2. Verifique logs em `/admin/logs`
3. Confirme recebimento no WhatsApp

## 📱 Templates Disponíveis

### u-ETG (Aprovado)
- **Nome:** `uetg_paciente_agenda_ptbr`
- **Parâmetros:** `{{1}}` = Nome, `{{2}}` = Data
- **Exemplo:** "Olá {{1}}, você tem exame u-ETG agendado para {{2}}"

## 🔍 Monitoramento

### Logs do Sistema
- **Interface:** `/admin/logs`
- **API:** `GET /admin/api/campaigns/{id}/runs`

### Métricas Dashboard
- Total de campanhas ativas
- Mensagens enviadas hoje
- Taxa de sucesso
- Próxima execução

## ⚠️ Troubleshooting

### Erro "Token inválido"
- Verifique `ADMIN_UI_TOKEN` no Railway
- Use header `X-Admin-Token` nas APIs

### Erro "Template não encontrado"
- Verifique se template está aprovado no Meta
- Confirme nome exato do template

### Scheduler não executa
- Verifique logs do Railway
- Confirme timezone `America/Sao_Paulo`
- Verifique se campanha está "active"

### Webhook não recebe
- Confirme `APP_SECRET` configurado
- Verifique URL do webhook no Meta
- Teste com ngrok localmente

## 🎯 Próximos Passos

1. **Teste completo** do sistema em produção
2. **Adicionar mais templates** conforme necessário
3. **Configurar alertas** para falhas
4. **Backup automático** do PostgreSQL
5. **Monitoramento** com logs estruturados

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique logs em `/admin/logs`
2. Teste health check em `/health`
3. Confirme variáveis de ambiente
4. Verifique status do Railway

---

**Sistema pronto para produção!** ✅

**Interface Admin:** `https://seu-app.up.railway.app/admin`
**Health Check:** `https://seu-app.up.railway.app/health`

