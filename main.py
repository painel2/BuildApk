import os
import time
import subprocess
import threading
import json
import urllib.request
import urllib.parse
import ssl
import random
from glob import glob

from kivy.app import App
from kivy.clock import Clock
from kivy.core.clipboard import Clipboard
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle


class ModernTextInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = (1, 1, 1, 1)
        self.cursor_color = (0.57, 0.21, 0.95, 1)
        self.padding = [15, 15, 15, 15]
        self.font_size = '15sp'
        
        with self.canvas.before:
            Color(0.12, 0.15, 0.22, 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class ModernButton(Button):
    def __init__(self, bg_color=(0.57, 0.21, 0.95, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = '14sp'
        self.bold = True
        self.custom_bg = bg_color
        
        with self.canvas.before:
            Color(*self.custom_bg)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class ClipAppLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10

        self.processo_ffmpeg = None
        self.gravando = False
        self.pasta_buffer = os.path.join(App.get_running_app().user_data_dir, "buffer")
        os.makedirs(self.pasta_buffer, exist_ok=True)

        # 1. Título
        self.add_widget(Label(
            text="Twitch Clipper [Direto]",
            font_size='22sp',
            bold=True,
            size_hint_y=None,
            height=35,
            color=(0.7, 0.3, 1, 1)
        ))

        # 2. Input
        self.input_canal = ModernTextInput(
            hint_text="twitch.tv/canal",
            multiline=False,
            size_hint_y=None,
            height=50
        )
        self.add_widget(self.input_canal)

        # 3. Botão Colar
        self.btn_colar = ModernButton(
            text="COLAR LINK",
            bg_color=(0.2, 0.25, 0.35, 1),
            size_hint_y=None,
            height=45
        )
        self.btn_colar.bind(on_press=self.colar_link)
        self.add_widget(self.btn_colar)

        # 4. Botão Iniciar / Parar
        self.btn_iniciar = ModernButton(
            text="INICIAR BUFFER (5 MIN)",
            bg_color=(0.4, 0.1, 0.7, 1),
            size_hint_y=None,
            height=50
        )
        self.btn_iniciar.bind(on_press=self.toggle_buffer)
        self.add_widget(self.btn_iniciar)

        # 5. Botão Salvar
        self.btn_clipar = ModernButton(
            text="SALVAR CLIPE",
            bg_color=(0.8, 0.15, 0.15, 1),
            size_hint_y=None,
            height=50
        )
        self.btn_clipar.disabled = True
        self.btn_clipar.bind(on_press=self.salvar_clipe)
        self.add_widget(self.btn_clipar)

        # 6. Caixa de Log / Debug na Tela
        self.add_widget(Label(
            text="Console de Erros / Debug:",
            font_size='12sp',
            size_hint_y=None,
            height=20,
            color=(0.5, 0.5, 0.6, 1),
            halign='left'
        ))

        self.console_debug = TextInput(
            text="App iniciado. Cole o link e clique em Iniciar.\n",
            readonly=True,
            multiline=True,
            background_color=(0.05, 0.07, 0.1, 1),
            foreground_color=(0.2, 1, 0.2, 1),
            font_size='12sp'
        )
        self.add_widget(self.console_debug)

        Clock.schedule_once(lambda dt: self.colar_link(None), 0.5)

    def log_debug(self, texto):
        def atualizar(dt):
            self.console_debug.text += f"> {texto}\n"
            self.console_debug.cursor = (len(self.console_debug.text), 0)
        Clock.schedule_once(atualizar)

    def colar_link(self, instance):
        try:
            texto_copiado = Clipboard.paste()
            if texto_copiado and len(texto_copiado.strip()) > 0:
                self.input_canal.text = texto_copiado.strip()
                self.log_debug("Link colado da área de transferência.")
        except Exception as e:
            self.log_debug(f"Erro ao colar: {str(e)}")

    def extrair_canal(self, entrada):
        entrada = entrada.strip()
        if "twitch.tv/" in entrada:
            canal = entrada.split("twitch.tv/")[-1].split("?")[0].replace("/", "")
            return canal.lower()
        elif not entrada.startswith("http"):
            return entrada.replace("/", "").lower()
        return entrada.strip("/").split("/")[-1].lower()

    def toggle_buffer(self, instance):
        if not self.gravando:
            entrada = self.input_canal.text.strip()
            if not entrada:
                self.log_debug("ERRO: Campo de link vazio!")
                return

            self.btn_iniciar.disabled = True
            canal = self.extrair_canal(entrada)
            self.log_debug(f"Buscando stream para o canal: {canal}")
            threading.Thread(target=self.iniciar_processo, args=(canal,), daemon=True).start()
        else:
            self.parar_buffer()

    def iniciar_processo(self, canal):
        try:
            self.log_debug("Gerando token de acesso à Twitch...")
            
            # IGNORA O ERRO DE SSL NO ANDROID (Certificados desatualizados)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

            # Requisição leve imitando cliente oficial para pegar a playlist m3u8
            client_id = "kimne78kx3ncx6brgo4mv6wki5h1ko"
            data_gql = json.dumps([{
                "operationName": "PlaybackAccessToken_Anonymous",
                "variables": {"isLive": True, "login": canal, "vodID": "", "isVod": False, "playerType": "embed"},
                "extensions": {"persistedQuery": {"version": 1, "sha256Hash": "0828119ded1c13477966434e15800ff571af1338a09b392484a7032fb3904cef"}}
            }]).encode('utf-8')

            req = urllib.request.Request("https://gql.twitch.tv/gql", data=data_gql, headers={
                "Client-ID": client_id,
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            })

            # Passa o contexto SSL customizado para burlar a trava do Android
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                res_json = json.loads(response.read().decode())
                stream_data = res_json[0]["data"]["streamPlaybackAccessToken"]
                token = stream_data["value"]
                sig = stream_data["signature"]

            self.log_debug("Token obtido! Montando link m3u8...")
            
            sub_ver = random.randint(1000, 9999)
            stream_url = f"https://usher.ttvnw.net/api/channel/hls/{canal}.m3u8?client_id={client_id}&token={urllib.parse.quote(token)}&sig={sig}&allow_source=true&fast_bread=true"

            Clock.schedule_once(lambda dt: self.iniciar_gravacao_ffmpeg(stream_url))

        except Exception as e:
            self.log_debug(f"EXCEÇÃO AO BUSCAR STREAM: {str(e)}")
            Clock.schedule_once(lambda dt: setattr(self.btn_iniciar, 'disabled', False))

    def iniciar_gravacao_ffmpeg(self, stream_url):
        caminho_ffmpeg = self.obter_caminho_ffmpeg()
        pattern = os.path.join(self.pasta_buffer, "segmento_%03d.ts")

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

        self.log_debug("Iniciando FFmpeg em segundo plano...")
        self.processo_ffmpeg = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.gravando = True

        self.btn_iniciar.text = "PARAR BUFFER"
        self.btn_iniciar.custom_bg = (0.3, 0.3, 0.3, 1)
        self.btn_iniciar.disabled = False
        self.btn_clipar.disabled = False
        self.log_debug("STATUS: Gravando buffer com sucesso!")

    def obter_caminho_ffmpeg(self):
        caminho_local = os.path.join(os.path.dirname(__file__), 'bin', 'ffmpeg')
        if os.path.exists(caminho_local):
            return caminho_local
        return 'ffmpeg'

    def parar_buffer(self):
        if self.processo_ffmpeg:
            self.processo_ffmpeg.terminate()
            self.processo_ffmpeg = None

        self.gravando = False
        self.btn_iniciar.text = "INICIAR BUFFER (5 MIN)"
        self.btn_iniciar.custom_bg = (0.4, 0.1, 0.7, 1)
        self.btn_clipar.disabled = True
        self.log_debug("Buffer parado pelo usuário.")

    def salvar_clipe(self, instance):
        if not self.gravando:
            return
        self.log_debug("Processando e salvando clipe...")
        threading.Thread(target=self.processar_clipe, daemon=True).start()

    def processar_clipe(self):
        try:
            segmentos = sorted(glob(os.path.join(self.pasta_buffer, "segmento_*.ts")), key=os.path.getmtime)
            if not segmentos:
                self.log_debug("ERRO: Nenhum segmento .ts gerado ainda.")
                return

            concat_list_path = os.path.join(self.pasta_buffer, "files.txt")
            with open(concat_list_path, "w") as f:
                for seg in segmentos:
                    f.write(f"file '{seg}'\n")

            pasta_download = "/sdcard/Download" if os.path.exists("/sdcard/Download") else self.pasta_buffer
            nome_arquivo = f"clipe_{int(time.time())}.mp4"
            caminho_saida = os.path.join(pasta_download, nome_arquivo)

            caminho_ffmpeg = self.obter_caminho_ffmpeg()
            cmd_concat = [
                caminho_ffmpeg, '-y', '-f', 'concat', '-safe', '0',
                '-i', concat_list_path, '-c', 'copy', caminho_saida
            ]
            subprocess.run(cmd_concat, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.log_debug(f"SUCESSO! Clipe salvo em: {caminho_saida}")
        except Exception as e:
            self.log_debug(f"EXCEÇÃO AO SALVAR: {str(e)}")


class TwitchApp(App):
    def build(self):
        from kivy.core.window import Window
        Window.clearcolor = (0.07, 0.09, 0.13, 1)
        return ClipAppLayout()

    def on_stop(self):
        if hasattr(self.root, 'processo_ffmpeg') and self.root.processo_ffmpeg:
            self.root.processo_ffmpeg.terminate()


if __name__ == '__main__':
    TwitchApp().run()
