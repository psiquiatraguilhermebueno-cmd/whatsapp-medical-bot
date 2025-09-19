#!/usr/bin/env python3
"""
Script definitivo para cadastrar paciente Guilherme Bueno e testar sistema completo
"""

import os
import sys
import requests
import json
from datetime import datetime, timedelta
import sqlite3

# Configurações
RAILWAY_URL = "https://web-production-4fc41.up.railway.app"
ADMIN_TOKEN = "admin123456"
PATIENT_NAME = "Guilherme Bueno"
PATIENT_PHONE = "+5514997799022"

# Tokens WhatsApp (das variáveis de ambiente configuradas)
WHATSAPP_ACCESS_TOKEN = "EAANTZCXB0csgBPft9y6ZBIdeTVM5PVLr2ZBZAlTGd49ezcAklZCF4DDZC6r6NQ4nrDREkNnC6iEebI7YxciceIMF9BD9Cwp8OqVpBYxeZB2gAZADsVQZCsDbDZAlaPZC3iByj0ZAn2eaSrmjPaQPqZBX6UJZAK6Hd8MuXGoKVrLFPooE7so4G1w2wYNaxJYn1SgQ6RnwZDZD"
WHATSAPP_PHONE_NUMBER_ID = "797803706754193"
UETG_TEMPLATE_NAME = "uetg_paciente_agenda_ptbr"

def test_health_check():
    """Testa se a aplicação está funcionando"""
    try:
        response = requests.get(f"{RAILWAY_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health Check OK: {data}")
            return True
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
        return False

def register_patient_via_api():
    """Cadastra o paciente via API"""
    try:
        # Dados do paciente
        patient_data = {
            "name": PATIENT_NAME,
            "phone": PATIENT_PHONE,
            "email": "guilherme@exemplo.com",
            "birth_date": "1990-01-01",
            "gender": "M",
            "protocols": {
                "uetg": {
                    "enabled": True,
                    "frequency": "random",
                    "time": "07:30",
                    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"]
                },
                "gad7": {
                    "enabled": True,
                    "frequency": "weekly",
                    "time": "09:00",
                    "days": ["monday"]
                },
                "phq9": {
                    "enabled": True,
                    "frequency": "weekly", 
                    "time": "10:00",
                    "days": ["tuesday"]
                },
                "asrs18": {
                    "enabled": True,
                    "frequency": "monthly",
                    "time": "11:00",
                    "days": ["monday"]
                }
            },
            "tags": ["uetg", "gad7", "phq9", "asrs18"],
            "active": True,
            "priority": "high",
            "notes": "Paciente de teste para sistema u-ETG e escalas psicológicas"
        }
        
        # Headers com token admin
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ADMIN_TOKEN}",
            "X-Admin-Token": ADMIN_TOKEN
        }
        
        # Tenta cadastrar via API
        response = requests.post(
            f"{RAILWAY_URL}/admin/api/patients",
            json=patient_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Paciente cadastrado com sucesso: {result}")
            return result.get("patient_id")
        else:
            print(f"❌ Erro ao cadastrar paciente: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def send_whatsapp_template(template_name, phone_number, parameters=None):
    """Envia template WhatsApp"""
    try:
        # URL da API do WhatsApp
        url = f"https://graph.facebook.com/v18.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Payload básico
        payload = {
            "messaging_product": "whatsapp",
            "to": phone_number.replace("+", ""),
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "pt_BR"}
            }
        }
        
        # Adiciona parâmetros se fornecidos
        if parameters:
            payload["template"]["components"] = [
                {
                    "type": "body",
                    "parameters": parameters
                }
            ]
        
        # Envia mensagem
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Template {template_name} enviado com sucesso: {result}")
            return result
        else:
            print(f"❌ Erro ao enviar template {template_name}: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao enviar template {template_name}: {e}")
        return None

def test_uetg_template():
    """Testa envio do template u-ETG"""
    print("\n🧪 Testando template u-ETG...")
    
    # Parâmetros para o template u-ETG
    parameters = [
        {"type": "text", "text": PATIENT_NAME},
        {"type": "text", "text": "07:30"},
        {"type": "text", "text": "08:30"},
        {"type": "text", "text": "09:30"}
    ]
    
    return send_whatsapp_template(UETG_TEMPLATE_NAME, PATIENT_PHONE, parameters)

def test_gad7_template():
    """Testa envio do template GAD-7"""
    print("\n😰 Testando template GAD-7...")
    
    # Template GAD-7 (se existir)
    return send_whatsapp_template("gad7_escala_ptbr", PATIENT_PHONE)

def test_phq9_template():
    """Testa envio do template PHQ-9"""
    print("\n😔 Testando template PHQ-9...")
    
    # Template PHQ-9 (se existir)
    return send_whatsapp_template("phq9_escala_ptbr", PATIENT_PHONE)

def create_response_webhook():
    """Cria webhook para receber respostas"""
    try:
        webhook_data = {
            "url": f"{RAILWAY_URL}/webhook/whatsapp",
            "verify_token": "verify_123"
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Admin-Token": ADMIN_TOKEN
        }
        
        response = requests.post(
            f"{RAILWAY_URL}/admin/api/webhook",
            json=webhook_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Webhook configurado com sucesso")
            return True
        else:
            print(f"❌ Erro ao configurar webhook: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao configurar webhook: {e}")
        return False

def main():
    """Função principal"""
    print("🚀 INICIANDO TESTE COMPLETO DO SISTEMA WHATSAPP u-ETG")
    print("=" * 60)
    
    # 1. Testa health check
    print("\n1️⃣ Testando Health Check...")
    if not test_health_check():
        print("❌ Sistema não está funcionando. Abortando.")
        return False
    
    # 2. Cadastra paciente
    print("\n2️⃣ Cadastrando paciente Guilherme Bueno...")
    patient_id = register_patient_via_api()
    if not patient_id:
        print("⚠️ Não foi possível cadastrar via API, mas continuando com testes...")
    
    # 3. Configura webhook
    print("\n3️⃣ Configurando webhook para respostas...")
    create_response_webhook()
    
    # 4. Testa templates WhatsApp
    print("\n4️⃣ Testando envio de templates WhatsApp...")
    
    # Template u-ETG
    uetg_result = test_uetg_template()
    
    # Template GAD-7
    gad7_result = test_gad7_template()
    
    # Template PHQ-9
    phq9_result = test_phq9_template()
    
    # 5. Resumo dos resultados
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES:")
    print("=" * 60)
    
    print(f"✅ Health Check: OK")
    print(f"{'✅' if patient_id else '⚠️'} Cadastro Paciente: {'OK' if patient_id else 'Parcial'}")
    print(f"{'✅' if uetg_result else '❌'} Template u-ETG: {'OK' if uetg_result else 'Falhou'}")
    print(f"{'✅' if gad7_result else '❌'} Template GAD-7: {'OK' if gad7_result else 'Falhou'}")
    print(f"{'✅' if phq9_result else '❌'} Template PHQ-9: {'OK' if phq9_result else 'Falhou'}")
    
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Verifique se as mensagens chegaram no WhatsApp +5514997799022")
    print("2. Responda às mensagens conforme solicitado")
    print("3. O sistema deve enviar notificações automáticas para o admin")
    print("4. Verifique o painel admin para ver as respostas armazenadas")
    
    print(f"\n🔗 LINKS ÚTEIS:")
    print(f"• Painel Admin: {RAILWAY_URL}/admin")
    print(f"• Health Check: {RAILWAY_URL}/health")
    print(f"• Webhook: {RAILWAY_URL}/webhook/whatsapp")
    
    return True

if __name__ == "__main__":
    main()
