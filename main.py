import re
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.clock import mainthread
import threading

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, VideoUnavailable

class SubtitleApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10

        # Título
        self.add_widget(Label(
            text="[b]Puxador de Legendas do YT[/b]", 
            markup=True, 
            font_size='20sp', 
            size_hint_y=None, 
            height=40
        ))

        # Campo de entrada (Link ou ID)
        self.url_input = TextInput(
            hint_text="Cole o link do YouTube ou ID aqui...",
            multiline=False,
            size_hint_y=None,
            height=50,
            padding=[10, 15]
        )
        self.add_widget(self.url_input)

        # Botão de Buscar
        self.btn_buscar = Button(
            text="Baixar Legenda",
            size_hint_y=None,
            height=50
        )
        self.btn_buscar.bind(on_press=self.iniciar_busca)
        self.add_widget(self.btn_buscar)

        # Área com Scroll para exibir o texto
        scroll = ScrollView(size_hint=(1, 1))
        self.result_label = Label(
            text="A legenda aparecerá aqui...",
            size_hint_y=None,
            text_size=(None, None),
            valign='top',
            halign='left',
            padding=[10, 10]
        )
        self.result_label.bind(
            texture_size=lambda instance, value: setattr(instance, 'height', value[1])
        )
        self.result_label.bind(
            width=lambda instance, value: setattr(instance, 'text_size', (value, None))
        )
        scroll.add_widget(self.result_label)
        self.add_widget(scroll)

    def extrair_id(self, url_ou_id):
        url_ou_id = url_ou_id.strip()
        # Regex para extrair ID de 11 caracteres de links normais e curtos
        padrao = r'(?:v=|\/|youtu\.be\/)([a-zA-Z0-9_-]{11})'
        match = re.search(padrao, url_ou_id)
        if match:
            return match.group(1)
        if len(url_ou_id) == 11:
            return url_ou_id
        return None

    def iniciar_busca(self, instance):
        url = self.url_input.text
        video_id = self.extrair_id(url)

        if not video_id:
            self.atualizar_texto("❌ Link ou ID do YouTube inválido!")
            return

        self.atualizar_texto("⏳ Buscando legenda, aguarde...")
        self.btn_buscar.disabled = True

        # Roda a busca em uma Thread separada para não travar a tela
        threading.Thread(target=self.buscar_legenda, args=(video_id,)).start()

    def buscar_legenda(self, video_id):
        try:
            transcript = YouTubeTranscriptApi().fetch(video_id, languages=["pt", "en"])
            
            linhas = []
            for snippet in transcript:
                m = int(snippet.start // 60)
                s = int(snippet.start % 60)
                linhas.append(f"[{m:02d}:{s:02d}] {snippet.text}")
            
            texto_final = "\n".join(linhas)
            self.atualizar_texto(texto_final)

        except TranscriptsDisabled:
            self.atualizar_texto("❌ Esse vídeo está com as legendas desativadas.")
        except VideoUnavailable:
            self.atualizar_texto("❌ Vídeo indisponível ou não encontrado.")
        except Exception as e:
            self.atualizar_texto(f"❌ Erro ao buscar legenda: {str(e)}")
        finally:
            self.liberar_botao()

    @mainthread
    def atualizar_texto(self, texto):
        self.result_label.text = texto

    @mainthread
    def liberar_botao(self):
        self.btn_buscar.disabled = False


class MainApp(App):
    def build(self):
        self.title = "Legendas YT"
        return SubtitleApp()

if __name__ == '__main__':
    MainApp().run()
