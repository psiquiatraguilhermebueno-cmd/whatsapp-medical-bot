# 🚀 README Operacional - Railway Deploy

## Configuração de Variáveis de Ambiente

### Variáveis Obrigatórias
```
WHATSAPP_ACCESS_TOKEN=seu_token_aqui
WHATSAPP_PHONE_NUMBER_ID=seu_phone_id_aqui
APP_SECRET=seu_app_secret_aqui
WHATSAPP_WEBHOOK_VERIFY_TOKEN=verify_123
```

### Variáveis u-ETG
```
ADMIN_PHONE_NUMBER=5514997799022
UETG_PATIENT_PHONE=numero_do_paciente
UETG_PATIENT_NAME=Nome do Paciente
UETG_DEFAULT_SLOT=07:30
```

### Variáveis Opcionais
```
DISABLE_SCHEDULER=1  # Para desabilitar agendamento automático
```

## Endpoints de Teste

### 1. Health Check
```bash
curl https://SEU-DOMINIO-RAILWAY.app/api/admin/health
```

### 2. Status do Sistema u-ETG
```bash
curl "https://SEU-DOMINIO-RAILWAY.app/api/admin/uetg/status?token=verify_123"
```

### 3. Forçar Sorteio
```bash
curl -X POST "https://SEU-DOMINIO-RAILWAY.app/api/admin/cron/uetg/plan?token=verify_123"
```

### 4. Forçar Envio (se hoje for dia sorteado)
```bash
curl -X POST "https://SEU-DOMINIO-RAILWAY.app/api/admin/cron/uetg/send?token=verify_123"
```

### 5. Teste de Template Manual
```bash
curl -X POST "https://graph.facebook.com/v18.0/SEU_PHONE_ID/messages" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messaging_product": "whatsapp",
    "to": "NUMERO_DESTINO",
    "type": "template",
    "template": {
      "name": "uetg_paciente_agenda_ptbr",
      "language": {"code": "pt_BR"},
      "components": [
        {
          "type": "body",
          "parameters": [
            {"type": "text", "text": "João Silva"},
            {"type": "text", "text": "15/01/2025"},
            {"type": "text", "text": "07:30"}
          ]
        }
      ]
    }
  }'
```

## Fluxo Automático

### Agendamento
- **Sábados 12:00**: Sorteia 2 datas úteis da próxima semana
- **Segunda a Sexta 07:00**: Envia lembrete se hoje for dia sorteado

### Logs Esperados
```
✅ u-ETG Config OK - Admin: 5514997799022, Patient: João Silva
✅ uETG Scheduler started.
📅 Sorteio: Sábados às 12:00
📨 Envio: Segunda a Sexta às 07:00
```

## Teste do Fluxo Completo

### 1. Verificar Deploy
- Acesse os logs do Railway
- Procure por "✅ uETG Scheduler started."

### 2. Testar Sorteio
```bash
curl -X POST "https://SEU-DOMINIO.app/api/admin/cron/uetg/plan?token=verify_123"
```
- Admin deve receber mensagem com 2 datas sorteadas

### 3. Testar Envio
```bash
curl -X POST "https://SEU-DOMINIO.app/api/admin/cron/uetg/send?token=verify_123"
```
- Se hoje for dia sorteado: paciente recebe template
- Admin recebe notificação de envio

### 4. Testar Botões
- Paciente clica em um horário (07:30, 12:00, 16:40, 19:00)
- Paciente recebe confirmação
- Admin recebe notificação da confirmação

## Troubleshooting

### Erro: 'NoneType' object has no attribute 'strip'
- Verificar se todas as variáveis de ambiente estão configuradas
- Usar o endpoint `/api/admin/uetg/status` para diagnóstico

### Scheduler não inicia
- Verificar logs do Railway
- Confirmar variáveis WHATSAPP_ACCESS_TOKEN e WHATSAPP_PHONE_NUMBER_ID

### Template não envia
- Verificar se template está aprovado no Meta
- Confirmar número do paciente está correto
- Verificar logs de erro no Railway

### Botões não funcionam
- Verificar se webhook está recebendo mensagens interativas
- Confirmar mapeamento de horários no código
- Verificar logs do handler

## Comandos Úteis

### Ver logs em tempo real (Railway CLI)
```bash
railway logs --follow
```

### Reiniciar aplicação
```bash
railway restart
```

### Verificar variáveis
```bash
railway variables
```

