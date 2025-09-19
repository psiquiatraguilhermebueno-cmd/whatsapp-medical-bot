#!/usr/bin/env python3
"""
Script para testar templates WhatsApp do sistema médico
"""

import os
import sys
import requests
import json
from datetime import datetime

# Configurações
RAILWAY_URL = "https://web-production-4fc41.up.railway.app"
ADMIN_TOKEN = "admin123456"
PATIENT_PHONE = "5514997799022"  # Guilherme Bueno

# Tokens WhatsApp
WHATSAPP_ACCESS_TOKEN = "EAANTZCXB0csgBPft9y6ZBIdeTVM5PVLr2ZBZAlTGd49ezcAklZCF4DDZC6r6NQ4nrDREkNnC6iEebI7YxciceIMF9BD9Cwp8OqVpBYxeZB2gAZADsVQZCsDbDZAlaPZC3iByj0ZAn2eaSrmjPaQPqZBX6UJZAK6Hd8MuXGoKVrLFPooE7so4G1w2wYNaxJYn1SgQ6RnwZDZD"
WHATSAPP_PHONE_NUMBER_ID = "797803706754193"

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
            "to": phone_number,
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
        
        print(f"🚀 Enviando template {template_name} para {phone_number}...")
        print(f"📋 Payload: {json.dumps(payload, indent=2)}")
        
        # Envia mensagem
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Template {template_name} enviado com sucesso!")
            print(f"📱 Message ID: {result.get('messages', [{}])[0].get('id', 'N/A')}")
            return result
        else:
            print(f"❌ Erro ao enviar template {template_name}: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao enviar template {template_name}: {e}")
        return None

def test_uetg_template():
    """Testa template u-ETG"""
    print("\n🧪 TESTANDO TEMPLATE u-ETG")
    print("=" * 50)
    
    # Parâmetros para o template u-ETG
    parameters = [
        {"type": "text", "text": "Guilherme Bueno"},
        {"type": "text", "text": "07:30"},
        {"type": "text", "text": "08:30"},
        {"type": "text", "text": "09:30"}
    ]
    
    return send_whatsapp_template("uetg_paciente_agenda_ptbr", PATIENT_PHONE, parameters)

def test_gad7_template():
    """Testa template GAD-7"""
    print("\n😰 TESTANDO TEMPLATE GAD-7")
    print("=" * 50)
    
    # Parâmetros para GAD-7
    parameters = [
        {"type": "text", "text": "Guilherme Bueno"},
        {"type": "text", "text": "Escala de Ansiedade Generalizada"}
    ]
    
    # Tenta diferentes nomes de template
    template_names = [
        "gad7_escala_ptbr",
        "gad_7_questionario_ptbr", 
        "ansiedade_gad7_ptbr",
        "escala_ansiedade_ptbr"
    ]
    
    for template_name in template_names:
        result = send_whatsapp_template(template_name, PATIENT_PHONE, parameters)
        if result:
            return result
        print(f"⚠️ Template {template_name} não encontrado, tentando próximo...")
    
    return None

def test_phq9_template():
    """Testa template PHQ-9"""
    print("\n😔 TESTANDO TEMPLATE PHQ-9")
    print("=" * 50)
    
    # Parâmetros para PHQ-9
    parameters = [
        {"type": "text", "text": "Guilherme Bueno"},
        {"type": "text", "text": "Escala de Depressão"}
    ]
    
    # Tenta diferentes nomes de template
    template_names = [
        "phq9_escala_ptbr",
        "phq_9_questionario_ptbr",
        "depressao_phq9_ptbr",
        "escala_depressao_ptbr"
    ]
    
    for template_name in template_names:
        result = send_whatsapp_template(template_name, PATIENT_PHONE, parameters)
        if result:
            return result
        print(f"⚠️ Template {template_name} não encontrado, tentando próximo...")
    
    return None

def test_asrs18_template():
    """Testa template ASRS-18"""
    print("\n🧠 TESTANDO TEMPLATE ASRS-18")
    print("=" * 50)
    
    # Parâmetros para ASRS-18
    parameters = [
        {"type": "text", "text": "Guilherme Bueno"},
        {"type": "text", "text": "Escala de TDAH"}
    ]
    
    # Tenta diferentes nomes de template
    template_names = [
        "asrs18_escala_ptbr",
        "asrs_18_questionario_ptbr",
        "tdah_asrs18_ptbr",
        "escala_tdah_ptbr"
    ]
    
    for template_name in template_names:
        result = send_whatsapp_template(template_name, PATIENT_PHONE, parameters)
        if result:
            return result
        print(f"⚠️ Template {template_name} não encontrado, tentando próximo...")
    
    return None

def register_patient_via_api():
    """Registra paciente via API corrigida"""
    print("\n👤 REGISTRANDO PACIENTE VIA API")
    print("=" * 50)
    
    try:
        # Dados do paciente
        patient_data = {
            "name": "Guilherme Bueno",
            "phone": "(14) 99779-9022",
            "email": "guilherme@exemplo.com",
            "birth_date": "1990-01-01",
            "gender": "M",
            "protocols": {
                "uetg": {
                    "enabled": True,
                    "frequency": "random",
                    "time": "07:30"
                },
                "gad7": {
                    "enabled": True,
                    "frequency": "weekly",
                    "time": "09:00"
                },
                "phq9": {
                    "enabled": True,
                    "frequency": "weekly", 
                    "time": "10:00"
                },
                "asrs18": {
                    "enabled": True,
                    "frequency": "monthly",
                    "time": "11:00"
                }
            },
            "priority": "high",
            "notes": "Paciente de teste para sistema u-ETG e escalas psicológicas",
            "active": True
        }
        
        # Headers com token admin
        headers = {
            "Content-Type": "application/json",
            "X-Admin-Token": ADMIN_TOKEN
        }
        
        print(f"📤 Enviando dados do paciente...")
        
        # Registra paciente
        response = requests.post(
            f"{RAILWAY_URL}/admin/api/patients",
            json=patient_data,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"✅ Paciente registrado com sucesso!")
            print(f"👤 ID: {result.get('patient', {}).get('id')}")
            print(f"📱 Telefone: {result.get('patient', {}).get('phone_masked')}")
            return result.get('patient', {}).get('id')
        else:
            print(f"❌ Erro ao registrar paciente: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def main():
    """Função principal"""
    print("🚀 TESTE COMPLETO DE TEMPLATES WHATSAPP")
    print("=" * 60)
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🌐 URL: {RAILWAY_URL}")
    print(f"📱 Telefone: {PATIENT_PHONE}")
    print("=" * 60)
    
    # 1. Registrar paciente
    patient_id = register_patient_via_api()
    
    # 2. Testar templates
    print("\n📋 TESTANDO TEMPLATES WHATSAPP")
    print("=" * 60)
    
    # Template u-ETG (obrigatório)
    uetg_result = test_uetg_template()
    
    # Template GAD-7
    gad7_result = test_gad7_template()
    
    # Template PHQ-9
    phq9_result = test_phq9_template()
    
    # Template ASRS-18
    asrs18_result = test_asrs18_template()
    
    # 3. Resumo dos resultados
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    print(f"{'✅' if patient_id else '❌'} Registro Paciente: {'OK' if patient_id else 'FALHOU'}")
    print(f"{'✅' if uetg_result else '❌'} Template u-ETG: {'OK' if uetg_result else 'FALHOU'}")
    print(f"{'✅' if gad7_result else '❌'} Template GAD-7: {'OK' if gad7_result else 'FALHOU'}")
    print(f"{'✅' if phq9_result else '❌'} Template PHQ-9: {'OK' if phq9_result else 'FALHOU'}")
    print(f"{'✅' if asrs18_result else '❌'} Template ASRS-18: {'OK' if asrs18_result else 'FALHOU'}")
    
    # Próximos passos
    print("\n🎯 PRÓXIMOS PASSOS:")
    print("1. Verifique se as mensagens chegaram no WhatsApp +5514997799022")
    print("2. Responda às mensagens conforme solicitado")
    print("3. Verifique o painel admin para monitorar as respostas")
    print("4. Configure templates ausentes no Facebook Business Manager")
    
    print(f"\n🔗 LINKS ÚTEIS:")
    print(f"• Painel Admin: {RAILWAY_URL}/admin")
    print(f"• Health Check: {RAILWAY_URL}/health")
    print(f"• Lista Pacientes: {RAILWAY_URL}/admin/patients")
    
    return True

if __name__ == "__main__":
    main()
