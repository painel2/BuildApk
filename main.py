import os
import shutil
import subprocess
import threading
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput


class TwitchClipperApp(App):

  def build(self):
    self.rodando_buffer = False
    self.processo_ffmpeg = None

    layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

    # Título
    layout.add_widget(
        Label(
            text='🎬 Twitch Clip Buffer (5 Min)',
            font_size='22sp',
            bold=True,
            size_hint_y=None,
            height=50,
        )
    )

    # Campo para colar a URL do stream / m3u8
    self.input_url = TextInput(
        hint_text='Cole aqui o link do stream (.m3u8) da live...',
        multiline=False,
        size_hint_y=None,
        height=50,
    )
    layout.add_widget(self.input_url)

    # Botão 1: Ligar / Desligar Gravação
    self.btn_toggle = Button(
        text='▶️ Iniciar Buffer (Fundo)',
        background_color=(0.2, 0.7, 0.3, 1),
        size_hint_y=None,
        height=60,
    )
    self.btn_toggle.bind(on_press=self.toggle_buffer)
    layout.add_widget(self.btn_toggle)

    # Botão 2: CLIPAR (Salvar o que já passou)
    self.btn_clip = Button(
        text='✂️ CLIPAR (Salvar últimos 5 min)',
        font_size='18sp',
        bold=True,
        background_color=(0.9, 0.3, 0.2, 1),
        size_hint_y=None,
        height=80,
    )
    self.btn_clip.bind(on_press=self.salvar_clipe)
    layout.add_widget(self.btn_clip)

    # Status
    self.lbl_status = Label(
        text='Status: Parado', font_size='14sp', color=(0.8, 0.8, 0.8, 1)
    )
    layout.add_widget(self.lbl_status)

    self.preparar_pastas()
    return layout

  def obter_caminho_ffmpeg(self):
    """Localiza o executável do FFmpeg que foi embutido na pasta bin/ dentro do APK"""
    caminho_local = os.path.join(
        os.path.dirname(__file__), 'bin', 'ffmpeg-arm64'
    )
    if not os.path.exists(caminho_local):
      # Fallback caso a pasta se chame apenas ffmpeg
      caminho_local = os.path.join(os.path.dirname(__file__), 'bin', 'ffmpeg')

    # Da permissão de execução no Android
    try:
      os.chmod(caminho_local, 0o755)
    except Exception:
      pass

    return caminho_local

  def preparar_pastas(self):
    """Cria a pasta temporária do buffer e a pasta final de Downloads"""
    self.dir_buffer = os.path.join(self.user_data_dir, 'temp_buffer')
    os.makedirs(self.dir_buffer, exist_ok=True)
    self.arquivo_buffer = os.path.join(self.dir_buffer, 'buffer_5min.mp4')

    # Pasta de destino pública no celular
    self.dir_downloads = '/storage/emulated/0/Download/TwitchClips'
    os.makedirs(self.dir_downloads, exist_ok=True)

  def toggle_buffer(self, instance):
    if not self.rodando_buffer:
      url = self.input_url.text.strip()
      if not url:
        self.lbl_status.text = '⚠️ Cole o link do stream (.m3u8) primeiro!'
        return

      self.rodando_buffer = True
      self.btn_toggle.text = '⏹️ Parar Gravador'
      self.btn_toggle.background_color = (0.7, 0.2, 0.2, 1)
      self.lbl_status.text = '🟢 Buffer Ativo! Gravando em loop...'

      threading.Thread(
          target=self.rodar_ffmpeg_loop, args=(url,), daemon=True
      ).start()
    else:
      self.parar_buffer()

  def rodar_ffmpeg_loop(self, url):
    ffmpeg_bin = self.obter_caminho_ffmpeg()

    # Comando FFmpeg: grava a stream e limita em 300 segundos (5 minutos)
    cmd = [
        ffmpeg_bin,
        '-y',
        '-i',
        url,
        '-c',
        'copy',
        '-t',
        '300',
        self.arquivo_buffer,
    ]

    while self.rodando_buffer:
      self.processo_ffmpeg = subprocess.Popen(
          cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
      )
      self.processo_ffmpeg.wait()

  def parar_buffer(self):
    self.rodando_buffer = False
    if self.processo_ffmpeg:
      self.processo_ffmpeg.terminate()
    self.btn_toggle.text = '▶️ Iniciar Buffer (Fundo)'
    self.btn_toggle.background_color = (0.2, 0.7, 0.3, 1)
    self.lbl_status.text = '🔴 Buffer parado.'

  def salvar_clipe(self, instance):
    if (
        not os.path.exists(self.arquivo_buffer)
        or os.path.getsize(self.arquivo_buffer) == 0
    ):
      self.lbl_status.text = (
          '⚠️ Aguarde alguns segundos para o buffer acumular vídeo...'
      )
      return

    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    nome_arquivo = f'Clipe_{timestamp}.mp4'
    destino = os.path.join(self.dir_downloads, nome_arquivo)

    try:
      shutil.copy(self.arquivo_buffer, destino)
      self.lbl_status.text = '✅ Clipe salvo em Downloads/TwitchClips!'
    except Exception as e:
      self.lbl_status.text = f'❌ Erro ao salvar: {str(e)}'


if __name__ == '__main__':
  TwitchClipperApp().run()
