import os
import time
import threading
import requests
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

class TwitchClipApp(App):
    def build(self):
        self.rodando = False

        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        layout.add_widget(Label(
            text="🎬 Twitch Clip App", 
            font_size='22sp', 
            bold=True,
            size_hint_y=None, 
            height=50
        ))

        self.input_url = TextInput(
            hint_text="Cole o link da live ou do fluxo (.m3u8) aqui...",
            multiline=False,
            size_hint_y=None,
            height=50
        )
        layout.add_widget(self.input_url)

        self.btn_clip = Button(
            text="✂️ SALVAR CLIPE (5 MINUTOS)",
            font_size='18sp',
            bold=True,
            background_color=(0.2, 0.6, 0.9, 1),
            size_hint_y=None,
            height=80
        )
        self.btn_clip.bind(on_press=self.salvar_clipe)
        layout.add_widget(self.btn_clip)

        self.lbl_status = Label(
            text="Status: Pronto para uso",
            font_size='14sp',
            color=(0.8, 0.8, 0.8, 1)
        )
        layout.add_widget(self.lbl_status)

        self.preparar_pastas()
        return layout

    def preparar_pastas(self):
        try:
            from android.storage import primary_external_storage_path
            caminho_base = primary_external_storage_path()
            self.dir_clipes = os.path.join(caminho_base, "Download", "TwitchClips")
        except ImportError:
            self.dir_clipes = os.path.join(os.path.expanduser("~"), "Downloads", "TwitchClips")

        os.makedirs(self.dir_clipes, exist_ok=True)

    def salvar_clipe(self, instance):
        url = self.input_url.text.strip()
        if not url:
            self.lbl_status.text = "⚠️ Cole um link válido primeiro!"
            return

        self.lbl_status.text = "⏳ Baixando clipe em segundo plano..."
        threading.Thread(target=self.download_stream, args=(url,), daemon=True).start()

    def download_stream(self, url):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            nome_arquivo = f"Clipe_{timestamp}.mp4"
            caminho = os.path.join(self.dir_clipes, nome_arquivo)

            # Faz o download direto do fluxo
            response = requests.get(url, stream=True, timeout=15)
            with open(caminho, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            self.lbl_status.text = f"✅ Salvo em Downloads/TwitchClips!"
        except Exception as e:
            self.lbl_status.text = f"❌ Erro: {str(e)}"

if __name__ == "__main__":
    TwitchClipApp().run()
