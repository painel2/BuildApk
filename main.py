import os
import time
import subprocess
import threading
from glob import glob
from flask import Flask, render_template, request, jsonify

import streamlink
from kivy.app import App
from kivy.utils import platform

# Cria o servidor Flask interno
server = Flask(__name__)

pasta_buffer = ""
processo_ffmpeg = None
gravando = False

def obter_caminho_ffmpeg():
    caminho_local = os.path.join(os.path.dirname(__file__), 'bin', 'ffmpeg')
    if os.path.exists(caminho_local):
        return caminho_local
    return 'ffmpeg'

@server.route('/')
def index():
    return render_template('index.html')

@server.route('/api/iniciar', methods=['POST'])
def iniciar_buffer():
    global processo_ffmpeg, gravando, pasta_buffer
    
    dados = request.get_json()
    canal = dados.get('canal', '').strip()
    
    if not canal:
        return jsonify({'status': 'erro', 'mensagem': 'Digite o nome do canal!'}), 400

    try:
        url_canal = f"https://www.twitch.tv/{canal}" if not canal.startswith("http") else canal
        session = streamlink.Streamlink()
        session.set_option("http-headers", {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        streams = session.streams(url_canal)
        if "best" not in streams and "live" not in streams:
            return jsonify({'status': 'erro', 'mensagem': 'Live offline ou canal não encontrado!'}), 404

        stream_url = streams.get("best", streams.get("live")).url
        
        caminho_ffmpeg = obter_caminho_ffmpeg()
        pattern = os.path.join(pasta_buffer, "segmento_%03d.ts")

        cmd = [
            caminho_ffmpeg,
            '-y',
            '-user_agent', 'Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36',
            '-i', stream_url,
            '-c', 'copy',
            '-f', 'segment',
            '-segment_time', '5',
            '-segment_wrap', '60',
            '-reset_timestamps', '1',
            pattern
        ]

        processo_ffmpeg = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        gravando = True
        return jsonify({'status': 'sucesso', 'mensagem': f'Buffer iniciado para {canal}!'})

    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500

@server.route('/api/parar', methods=['POST'])
def parar_buffer():
    global processo_ffmpeg, gravando
    if processo_ffmpeg:
        processo_ffmpeg.terminate()
        processo_ffmpeg = None
    gravando = False
    return jsonify({'status': 'sucesso', 'mensagem': 'Buffer interrompido.'})

@server.route('/api/clipar', methods=['POST'])
def clipar():
    global pasta_buffer, gravando
    if not gravando:
        return jsonify({'status': 'erro', 'mensagem': 'O buffer não está ativo!'}), 400

    try:
        segmentos = sorted(glob(os.path.join(pasta_buffer, "segmento_*.ts")), key=os.path.getmtime)
        if not segmentos:
            return jsonify({'status': 'erro', 'mensagem': 'Nenhum segmento capturado ainda.'}), 400

        concat_list_path = os.path.join(pasta_buffer, "files.txt")
        with open(concat_list_path, "w") as f:
            for seg in segmentos:
                f.write(f"file '{seg}'\n")

        pasta_download = "/sdcard/Download" if os.path.exists("/sdcard/Download") else pasta_buffer
        nome_arquivo = f"clipe_twitch_{int(time.time())}.mp4"
        caminho_saida = os.path.join(pasta_download, nome_arquivo)

        caminho_ffmpeg = obter_caminho_ffmpeg()
        cmd_concat = [
            caminho_ffmpeg, '-y', '-f', 'concat', '-safe', '0',
            '-i', concat_list_path, '-c', 'copy', caminho_saida
        ]
        subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return jsonify({'status': 'sucesso', 'mensagem': f'Clipe salvo em: {nome_arquivo}'})
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500


# Inicialização da WebView no Kivy
from kivy.uix.boxlayout import BoxLayout

class WebApp(App):
    def build(self):
        global pasta_buffer
        pasta_buffer = os.path.join(self.user_data_dir, "buffer")
        os.makedirs(pasta_buffer, exist_ok=True)

        # Inicia o Flask em uma Thread separada
        threading.Thread(target=lambda: server.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False), daemon=True).start()

        # No Android, usa a WebView nativa via pyjnius
        if platform == 'android':
            from jnius import autoclass
            from android.runnable import run_on_ui_thread

            WebView = autoclass('android.webkit.WebView')
            WebViewClient = autoclass('android.webkit.WebViewClient')
            activity = autoclass('org.kivy.android.PythonActivity').mActivity

            @run_on_ui_thread
            def create_webview():
                webview = WebView(activity)
                webview.getSettings().setJavaScriptEnabled(True)
                webview.getSettings().setDomStorageEnabled(True)
                webview.setWebViewClient(WebViewClient())
                webview.loadUrl('http://127.0.0.1:5000')
                activity.setContentView(webview)

            create_webview()
            return BoxLayout()
        else:
            # No PC para testes
            import webbrowser
            webbrowser.open('http://127.0.0.1:5000')
            return BoxLayout()

if __name__ == '__main__':
    WebApp().run()
