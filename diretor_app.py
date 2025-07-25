import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

# =========================================================================
# --- INICIALIZAÇÃO E CONFIGURAÇÃO DA APLICAÇÃO FLASK ---
#
# NOME SUGERIDO PARA O ARQUIVO: diretor_app.py
#
# OBJETIVO: Este é o microsserviço "Diretor de IA". Sua única
# responsabilidade é receber um prompt complexo e detalhado do Orquestrador
# PHP e usar um modelo de linguagem avançado para reescrever o texto do
# usuário, injetando as tags de direção de voz (emoções, pausas, etc.).
# =========================================================================
app = Flask(__name__)
# Habilita CORS para permitir requisições do seu orquestrador PHP
CORS(app)

# Carrega a lista completa de tags de emoção/estilo para referência da IA.
# Isso garante que a IA saiba quais ferramentas ela pode usar na direção.
try:
    with open('emocoes.json', 'r', encoding='utf-8') as f:
        emotion_tags_data = json.load(f)
except FileNotFoundError:
    emotion_tags_data = {}

def get_all_tags_string():
    """Formata todas as tags disponíveis do emocoes.json em uma única string."""
    if not emotion_tags_data:
        return "Nenhuma tag disponível."
    
    all_tags = []
    for category in emotion_tags_data.values():
        for item in category:
            all_tags.append(item['comando'])
    
    all_tags.extend(['<breath>', '<emphasis_soft>', '<emphasis_medium>', '<emphasis_strong>'])
    return ", ".join(sorted(list(set(all_tags))))

# =========================================================================
# --- ROTAS DA API ---
# =========================================================================

@app.route('/')
def home():
    """Rota raiz para uma verificação simples de status."""
    return "Serviço Diretor de IA (analisador-l2gs) está online."

@app.route('/health')
def health_check():
    """Rota de Health Check para serviços de monitoramento (ex: UptimeRobot)."""
    return "API is awake and healthy.", 200

# -------------------------------------------------------------------------
# ROTA PRINCIPAL: O CÉREBRO DA DIREÇÃO DE VOZ
# -------------------------------------------------------------------------
@app.route('/api/humanize-text', methods=['POST'])
def humanize_text_endpoint():
    """
    Recebe um prompt final e detalhado do Orquestrador PHP e o utiliza
    para gerar um texto humanizado com tags de emoção e estilo.
    """
    # 1. Validação da Chave da API e dos Dados de Entrada
    # ----------------------------------------------------
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    if not gemini_api_key:
        return jsonify({"error": "Configuração do servidor Gemini incompleta."}), 500
    
    data = request.get_json()
    # [ALTERADO] A validação agora busca por 'prompt', não mais por 'text' ou 'humanization_level'.
    if not data or not data.get('prompt'):
        return jsonify({"error": "Requisição inválida. O 'prompt' não pode estar vazio."}), 400
    
    # 2. Extração do Prompt Final (Contrato simples com o PHP)
    # ----------------------------------------------------------
    final_prompt = data.get('prompt')
    
    # 3. Comunicação com a IA Generativa (Modelo de Linguagem)
    # -------------------------------------------------------
    try:
        genai.configure(api_key=gemini_api_key)
        # Usamos um modelo de linguagem poderoso para interpretar as instruções
        # complexas de direção e reescrever o texto.
        model = genai.GenerativeModel('gemini-1.5-pro-latest')
        
        available_tags = get_all_tags_string()
        
        # O prompt final é uma combinação do prompt do PHP com a lista de tags disponíveis.
        # Isso garante que a IA sempre saiba qual o seu "arsenal" de direção.
        prompt_com_ferramentas = (
            f"{final_prompt}\n\n"
            f"LEMBRE-SE: Sua resposta deve conter APENAS o texto modificado com as tags inseridas. "
            f"Não inclua nenhuma explicação, prefácio, ou qualquer texto adicional. "
            f"As tags de estilo e emoção que você pode usar são: {available_tags}."
        )

        response = model.generate_content(prompt_com_ferramentas)
        
        # 4. Processamento e Retorno da Resposta
        # -----------------------------------------
        humanized_text = response.text.strip()

        if not humanized_text:
             return jsonify({"error": "A IA retornou uma resposta vazia. Tente ajustar o texto ou o prompt."}), 500

        return jsonify({
            "success": True,
            "humanized_text": humanized_text
        })

    except Exception as e:
        print(f"Erro na API Gemini (Diretor de IA): {e}")
        return jsonify({"error": f"Erro interno ao processar o texto com a IA: {str(e)}"}), 500

# =========================================================================
# --- EXECUÇÃO DA APLICAÇÃO ---
# =========================================================================
if __name__ == '__main__':
    app.run(debug=True)