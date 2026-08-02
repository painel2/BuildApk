import os
import time
import subprocess
import threading
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
    """Campo de texto customizado com cantos arredondados"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = (1, 1, 1, 1)
        self.cursor_color = (0.57, 0.21, 0.95, 1)
        self.padding = [15, 15, 15, 15]
        self.font_size = '16sp'
        
        with self.canvas.before:
            Color(0.12, 0.15, 0.22, 1)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[12])
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size


class ModernButton(Button):
    """Botão customizado com cantos arredondados e cor personalizada"""
    def __init__(self, bg_color=(0.57, 0.21, 0.95, 1), **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.color = (1, 1, 1, 1)
        self.font_size = '16sp'
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
        self.padding = 20
        self.spacing = 15

        self.processo_ffmpeg = None
        self.gravando = False
        self.pasta_buffer = os.path.join(App.get_running_app().user_data_dir, "buffer")
        os.makedirs(self.pasta_buffer, exist_ok=True)

        # 1. Título do App
        self.add_widget(Label(
            text="[b]🎬 Twitch Clipper[/b]",
            markup=True,
            font_size='24sp',
            size_hint_y=None,
            height=40,
            color=(0.7, 0.3, 1, 1)
        ))

        # 2. Instrução rápida
        self.add_widget(Label(
            text="Cole a URL ou nome da live abaixo para iniciar a captura de 5 min.",
            font_size='13sp',
            color=(0.6, 0.6, 0.7, 1),
            halign='center'
        ))

        # 3. Campo de Entrada com suporte a URL completa
        self.input_canal = ModernTextInput(
            hint_text="Cole o link (ex: https://www.twitch.tv/facada)",
            multiline=False,
            size_hint_y=None,
            height=55
        )
        self.add_widget(self.input_canal)

        # 4. Botão Colar Automático (Para não precisar digitar nada!)
        self.btn_colar = ModernButton(
            text="📋 COLAR DA ÁREA DE TRANSFERÊNCIA",
            bg_color=(0.2, 0.25, 0.35, 1),
            size_hint_y=None,
            height=45
        )
        self.btn_colar.bind(on_press=self.colar_link)
        self.add_widget(self.btn_colar)

        # 5. Botão Iniciar / Parar Buffer
        self.btn_iniciar = ModernButton(
            text="▶ INICIAR BUFFER (5 MIN)",
            bg_color=(0.4, 0.1, 0.7, 1),
            size_hint_y=None,
            height=60
        )
        self.btn_iniciar.bind(on_press=self.toggle_buffer)
        self.add_widget(self.btn_iniciar)

        # 6. Botão de Salvar Clipe
        self.btn_clipar = ModernButton(
            text="✂️ SALVAR CLIPE",
            bg_color=(0.8, 0.15, 0.15, 1),
            size_hint_y=None,
            height=60
        )
        self.btn_clipar.disabled = True
        self.btn_clipar.bind(on_press=self.salvar_clipe)
        self.add_widget(self.btn_clipar)

        # 7. Label de Status
        self.status_label = Label(
            text="Status: Aguardando link...",
            font_size='13sp',
            size_hint_y=None,
            height=35,
            color=(0.7, 0.7, 0.7, 1)
        )
        self.add_widget(self.status_label)

        # Tenta pegar o link copiado assim que abre o app
        Clock.schedule_once(lambda dt: self.colar_link(None), 0.5)

    def colar_link(self, instance):
        try:
            texto_copiado = Clipboard.paste()
            if texto_copiado and ("twitch.tv" in texto_copiado or len(texto_copiado.strip()) > 0):
                self.input_canal.text = texto_copiado.strip()
                self.log("📋 Link colado automaticamente!")
        except Exception:
            pass

    def log(self, texto):
        Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', texto))

    def obter_caminho_ffmpeg(self):
        caminho_local = os.path.join(os.path.dirname(__file__), 'bin', 'ffmpeg')
        if os.path.exists(caminho_local):
            return caminho_local
        return 'ffmpeg'

    def extrair_url_ou_canal(self, entrada):
        entrada = entrada.strip()
        if "twitch.tv/" in entrada:
            # Pega o nome do canal se colou a URL inteira
            canal = entrada.split("twitch.tv/")[-1].split("?")[0].replace("/", "")
            return f"https://www.twitch.tv/{canal}"
        elif not entrada.startswith("http"):
            return f"https://www.twitch.tv/{entrada}"
        return entrada

    def toggle_buffer(self, instance):
        if not self.gravando:
            entrada = self.input_canal.text.strip()
            if not entrada:
                self.log("⚠️ Cole a URL da live primeiro!")
                return

            self.btn_iniciar.disabled = True
            url_final = self.extrair_url_ou_canal(entrada)
            self.log(f"🔎 Conectando à live...")
            threading.Thread(target=self.iniciar_processo, args=(url_final,), daemon=True).start()
        else:
            self.parar_buffer()

    def iniciar_processo(self, url_canal):
        try:
            import streamlink

            session = streamlink.Streamlink()
            session.set_option("http-headers", {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

            streams = session.streams(url_canal)
            if "best" not in streams and "live" not in streams:
                self.log("❌ Live offline ou link inválido!")
                Clock.schedule_once(lambda dt: setattr(self.btn_iniciar, 'disabled', False))
                return

            stream_url = streams.get("best", streams.get("live")).url
            Clock.schedule_once(lambda dt: self.iniciar_gravacao_ffmpeg(stream_url))

        except Exception as e:
            self.log(f"❌ Erro: {str(e)}")
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

        self.processo_ffmpeg = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.gravando = True

        self.btn_iniciar.text = "⏹ PARAR BUFFER"
        self.btn_iniciar.custom_bg = (0.3, 0.3, 0.3, 1)
        self.btn_iniciar.disabled = False
        self.btn_clipar.disabled = False
        self.log("🟢 Gravando buffer! Pode voltar pro app da Twitch.")

    def parar_buffer(self):
        if self.processo_ffmpeg:
            self.processo_ffmpeg.terminate()
            self.processo_ffmpeg = None

        self.gravando = False
        self.btn_iniciar.text = "▶ INICIAR BUFFER (5 MIN)"
        self.btn_iniciar.custom_bg = (0.4, 0.1, 0.7, 1)
        self.btn_clipar.disabled = True
        self.log("🔴 Buffer interrompido.")

    def salvar_clipe(self, instance):
        if not self.gravando:
            return
        self.log("✂️ Processando e salvando clipe...")
        threading.Thread(target=self.processar_clipe, daemon=True).start()

    def processar_clipe(self):
        try:
            segmentos = sorted(glob(os.path.join(self.pasta_buffer, "segmento_*.ts")), key=os.path.getmtime)
            if not segmentos:
                self.log("⚠️ Nenhum segmento gerado ainda.")
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
            self.log(f"🎉 Clipe salvo em Downloads/{nome_arquivo}")
        except Exception as e:
            self.log(f"❌ Erro ao salvar: {str(e)}")


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
