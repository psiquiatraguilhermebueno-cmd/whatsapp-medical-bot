# WhatsApp Medical Reminder Bot

Bot inteligente para lembretes médicos via WhatsApp, incluindo questionários clínicos, lembretes de medicação, registro de humor e exercícios de respiração.

## Funcionalidades

- 📋 **Escalas Clínicas**: PHQ-9, GAD-7, MDQ, ASRS, AUDIT, DAST-10
- 💊 **Lembretes de Medicação** com confirmação
- 😊 **Afetivograma** (registro diário de humor)
- 🫁 **Exercícios de Respiração** guiados por áudio
- 🏥 **Interface Administrativa** via WhatsApp
- 📊 **Relatórios** e alertas automáticos
- 🔒 **Segurança** com validação de webhook

## Pré-requisitos

- Python 3.8+
- Conta WhatsApp Business API
- ngrok (para testes locais)

## Instalação Local

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/whatsapp-medical-bot.git
cd whatsapp-medical-bot
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

### 4. Configure o WhatsApp Business API

1. Acesse https://developers.facebook.com/
2. Crie um aplicativo e configure o WhatsApp
3. Obtenha:
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `APP_SECRET` (nas configurações do app)
4. Defina um `WHATSAPP_VERIFY_TOKEN` (qualquer string segura)

### 5. Teste localmente com ngrok

```bash
# Terminal 1: Inicie o bot
python app.py

# Terminal 2: Exponha com ngrok
ngrok http 5000
```

### 6. Configure o webhook

1. No painel do WhatsApp Business API
2. Configure o webhook:
   - URL: `https://seu-ngrok-url.ngrok.io/api/whatsapp/webhook`
   - Verify Token: o valor de `WHATSAPP_VERIFY_TOKEN`
3. Assine o evento `messages`

## Deploy no Railway

### 1. Faça push para o GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Configure no Railway
1. Acesse https://railway.app/
2. Crie novo projeto → "Deploy from GitHub repo"
3. Selecione seu repositório
4. Configure as variáveis de ambiente:
   - `WHATSAPP_ACCESS_TOKEN`
   - `WHATSAPP_PHONE_NUMBER_ID`
   - `WHATSAPP_VERIFY_TOKEN`
   - `APP_SECRET`
   - `ADMIN_PHONE_NUMBER`

### 3. Atualize o webhook
- URL: `https://seu-app.up.railway.app/api/whatsapp/webhook`

## Uso

### Para Administradores
- `/menu` - Menu principal
- `/pacientes` - Gerenciar pacientes
- `/lembretes` - Configurar lembretes
- `/relatorios` - Ver relatórios
- `/add_paciente Nome` - Adicionar paciente

### Para Pacientes
- Recebem lembretes automáticos
- Respondem questionários com botões
- Confirmam medicações
- Registram humor diário

## Estrutura do Projeto

```
whatsapp-medical-bot/
├── src/
│   ├── models/          # Modelos de dados
│   ├── routes/          # Rotas da API
│   ├── services/        # Serviços WhatsApp
│   ├── utils/           # Utilitários
│   └── main.py          # Aplicação Flask
├── app.py               # Ponto de entrada
├── requirements.txt     # Dependências
├── .env.example         # Exemplo de configuração
└── README.md           # Este arquivo
```

## Segurança

- Validação de webhook com X-Hub-Signature-256
- Autenticação de administradores
- Dados criptografados em trânsito
- Conformidade com LGPD

## Suporte

Para dúvidas ou problemas, abra uma issue no GitHub.

## Licença

MIT License

