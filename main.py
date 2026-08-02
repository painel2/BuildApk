import os
import shutil
import threading
import subprocess
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

class TwitchClipApp(App):
    def build(self):
        self.rodando_buffer = False
        self.processo_ffmpeg = None

        # Layout Principal
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Título
        layout.add_widget(Label(
            text="🎬 Twitch Clip Buffer (5 Min)", 
            font_size='22sp', 
            bold=True,
            size_hint_y=None, 
            height=50
        ))

        # Campo de Texto para colocar a URL .m3u8 da live
        self.input_url = TextInput(
            hint_text="Cole o link .m3u8 do stream da Twitch aqui...",
            multiline=False,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.input_url)

        # Botão para Iniciar/Parar Buffer
        self.btn_toggle_buffer = Button(
            text="▶️ Iniciar Gravador de Buffer",
            background_color=(0.2, 0.7, 0.3, 1),
            size_hint_y=None,
            height=60
        )
        self.btn_toggle_buffer.bind(on_press=self.toggle_buffer)
        layout.add_widget(self.btn_toggle_buffer)

        # Botão Principal: SALVAR CLIPE
        self.btn_clip = Button(
            text="✂️ SALVAR ÚLTIMOS 5 MINUTOS",
            font_size='18sp',
            bold=True,
            background_color=(0.9, 0.3, 0.2, 1),
            size_hint_y=None,
            height=80
        )
        self.btn_clip.bind(on_press=self.salvar_clipe)
        layout.add_widget(self.btn_clip)

        # Label de Status
        self.lbl_status = Label(
            text="Status: Aguardando início...",
            font_size='14sp',
            color=(0.8, 0.8, 0.8, 1)
        )
        layout.add_widget(self.lbl_status)

        # Define pastas temporárias e de salvamento
        self.preparar_pastas()

        return layout

    def preparar_pastas(self):
        """Define e cria a pasta de armazenamento dos clipes no Android/PC."""
        self.dir_buffer = os.path.join(self.user_data_dir, "temp_buffer")
        os.makedirs(self.dir_buffer, exist_ok=True)
        self.arquivo_buffer = os.path.join(self.dir_buffer, "buffer_5min.mp4")

        # No Android, tenta salvar na pasta Download pública
        try:
            from android.storage import primary_external_storage_path
            caminho_base = primary_external_storage_path()
            self.dir_clipes = os.path.join(caminho_base, "Download", "TwitchClips")
        except ImportError:
            # Fallback para PC/Desktop
            self.dir_clipes = os.path.join(os.path.expanduser("~"), "Downloads", "TwitchClips")

        os.makedirs(self.dir_clipes, exist_ok=True)

    def toggle_buffer(self, instance):
        if not self.rodando_buffer:
            url = self.input_url.text.strip()
            if not url:
                self.lbl_status.text = "⚠️ Insira a URL .m3u8 da live primeiro!"
                return

            self.rodando_buffer = True
            self.btn_toggle_buffer.text = "⏹️ Parar Gravador"
            self.btn_toggle_buffer.background_color = (0.7, 0.2, 0.2, 1)
            self.lbl_status.text = "🟢 Gravação circular de 5min ATIVA..."

            # Inicia o FFmpeg em uma thread separada
            threading.Thread(target=self.rodar_ffmpeg_loop, args=(url,), daemon=True).start()
        else:
            self.parar_buffer()

    def rodar_ffmpeg_loop(self, url):
        """Roda o FFmpeg mantendo no máximo 300 segundos (5 min) no arquivo."""
        cmd = [
            "ffmpeg", "-y",
            "-i", url,
            "-c", "copy",
            "-t", "300",
            self.arquivo_buffer
        ]

        while self.rodando_buffer:
            self.processo_ffmpeg = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.processo_ffmpeg.wait()

    def parar_buffer(self):
        self.rodando_buffer = False
        if self.processo_ffmpeg:
            self.processo_ffmpeg.terminate()
        self.btn_toggle_buffer.text = "▶️ Iniciar Gravador de Buffer"
        self.btn_toggle_buffer.background_color = (0.2, 0.7, 0.3, 1)
        self.lbl_status.text = "🔴 Gravador parado."

    def salvar_clipe(self, instance):
        """Copia o buffer de 5min para a pasta Download do celular."""
        if not os.path.exists(self.arquivo_buffer) or os.path.getsize(self.arquivo_buffer) == 0:
            self.lbl_status.text = "⚠️ Aguarde alguns segundos até o buffer gerar dados..."
            return

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        nome_arquivo = f"Clipe_Twitch_{timestamp}.mp4"
        destino = os.path.join(self.dir_clipes, nome_arquivo)

        try:
            shutil.copy(self.arquivo_buffer, destino)
            self.lbl_status.text = f"✅ Clipe salvo em Downloads/TwitchClips!"
        except Exception as e:
            self.lbl_status.text = f"❌ Erro ao salvar: {str(e)}"

if __name__ == "__main__":
    TwitchClipApp().run()
