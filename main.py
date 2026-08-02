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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = (1, 1, 1, 1)
        self.cursor_color = (0.57, 0.21, 0.95, 1)
        self.padding = [15, 15, 15, 15]
        self.font_size = '14sp'
        
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


class DirectBufferLayout(BoxLayout):
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
            text="Buffer Direct .m3u8",
            font_size='22sp',
            bold=True,
            size_hint_y=None,
            height=35,
            color=(0.7, 0.3, 1, 1)
        ))

        # 2. Input do link .m3u8
        self.input_url = ModernTextInput(
            hint_text="Cole a URL .m3u8 aqui...",
            multiline=False,
            size_hint_y=None,
            height=50
        )
        self.add_widget(self.input_url)

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
            text="INICIAR BUFFER",
            bg_color=(0.4, 0.1, 0.7, 1),
            size_hint_y=None,
            height=50
        )
        self.btn_iniciar.bind(on_press=self.toggle_buffer)
        self.add_widget(self.btn_iniciar)

        # 5. Botão Salvar
        self.btn_clipar = ModernButton(
            text="SALVAR CLIPE (DOWNLOADS)",
            bg_color=(0.8, 0.15, 0.15, 1),
            size_hint_y=None,
            height=50
        )
        self.btn_clipar.disabled = True
        self.btn_clipar.bind(on_press=self.salvar_clipe)
        self.add_widget(self.btn_clipar)

        # 6. Console Log
        self.add_widget(Label(
            text="Status / Console:",
            font_size='12sp',
            size_hint_y=None,
            height=20,
            color=(0.5, 0.5, 0.6, 1)
        ))

        self.console_debug = TextInput(
            text="App pronto. Cole a URL .m3u8 e clique em Iniciar.\n",
            readonly=True,
            multiline=True,
            background_color=(0.05, 0.07, 0.1, 1),
            foreground_color=(0.2, 1, 0.2, 1),
            font_size='12sp'
        )
        self.add_widget(self.console_debug)

    def log_debug(self, texto):
        def atualizar(dt):
            self.console_debug.text += f"> {texto}\n"
            self.console_debug.cursor = (len(self.console_debug.text), 0)
        Clock.schedule_once(atualizar)

    def colar_link(self, instance):
        try:
            texto = Clipboard.paste()
            if texto:
                self.input_url.text = texto.strip().split('\n')[0]
                self.log_debug("Link colado.")
        except Exception as e:
            self.log_debug(f"Erro ao colar: {e}")

    def toggle_buffer(self, instance):
        if not self.gravando:
            url = self.input_url.text.strip()
            if not url or not url.startswith("http"):
                self.log_debug("ERRO: Cole uma URL m3u8 válida (começando com http)!")
                return

            self.limpar_pasta_buffer()
            self.iniciar_gravacao_ffmpeg(url)
        else:
            self.parar_buffer()

    def limpar_pasta_buffer(self):
        try:
            for f in glob(os.path.join(self.pasta_buffer, "*")):
                os.remove(f)
            self.log_debug("Pasta de buffer limpa.")
        except Exception as e:
            self.log_debug(f"Aviso ao limpar pasta: {e}")

    def iniciar_gravacao_ffmpeg(self, url):
        caminho_ffmpeg = self.obter_caminho_ffmpeg()
        pattern = os.path.join(self.pasta_buffer, "segmento_%03d.ts")

        cmd = [
            caminho_ffmpeg,
            '-y',
            '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            '-i', url,
            '-c', 'copy',
            '-f', 'segment',
            '-segment_time', '5',
            '-segment_wrap', '60',
            '-reset_timestamps', '1',
            pattern
        ]

        try:
            self.log_debug("Iniciando FFmpeg direto no stream...")
            self.processo_ffmpeg = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.gravando = True

            self.btn_iniciar.text = "PARAR BUFFER"
            self.btn_iniciar.custom_bg = (0.3, 0.3, 0.3, 1)
            self.btn_clipar.disabled = False
            self.log_debug("STATUS: Gravando buffer em tempo real!")
        except Exception as e:
            self.log_debug(f"ERRO ao chamar FFmpeg: {e}")

    def obter_caminho_ffmpeg(self):
        caminho_local = os.path.join(os.path.dirname(__file__), 'bin', 'ffmpeg')
        if os.path.exists(caminho_local):
            try:
                # Força a permissão de execução para o Android não bloquear o binário
                os.chmod(caminho_local, 0o755)
            except Exception:
                pass
            return caminho_local
        return 'ffmpeg'

    def parar_buffer(self):
        if self.processo_ffmpeg:
            self.processo_ffmpeg.terminate()
            self.processo_ffmpeg = None

        self.gravando = False
        self.btn_iniciar.text = "INICIAR BUFFER"
        self.btn_iniciar.custom_bg = (0.4, 0.1, 0.7, 1)
        self.btn_clipar.disabled = True
        self.log_debug("Buffer parado.")

    def salvar_clipe(self, instance):
        if not self.gravando and not glob(os.path.join(self.pasta_buffer, "segmento_*.ts")):
            self.log_debug("Nenhum buffer gravado para salvar.")
            return

        self.log_debug("Processando clipe...")
        threading.Thread(target=self.processar_clipe, daemon=True).start()

    def processar_clipe(self):
        try:
            segmentos = sorted(glob(os.path.join(self.pasta_buffer, "segmento_*.ts")), key=os.path.getmtime)
            if not segmentos:
                self.log_debug("ERRO: Nenhum segmento .ts encontrado.")
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
            self.log_debug(f"SUCESSO! Clipe salvo em:\n{caminho_saida}")
        except Exception as e:
            self.log_debug(f"EXCEÇÃO AO SALVAR: {e}")


class DirectApp(App):
    def build(self):
        from kivy.core.window import Window
        Window.clearcolor = (0.07, 0.09, 0.13, 1)
        return DirectBufferLayout()

    def on_stop(self):
        if hasattr(self.root, 'processo_ffmpeg') and self.root.processo_ffmpeg:
            self.root.processo_ffmpeg.terminate()


if __name__ == '__main__':
    DirectApp().run()
