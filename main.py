import os
import shutil
import threading
import time
import subprocess
from datetime import datetime

# URL do fluxo da Twitch (.m3u8) ou da live
# Obs: Para testes rápidos, você pode usar qualquer URL de stream HLS (.m3u8)
STREAM_URL = "SUA_URL_HLS_M3U8_AQUI" 

BUFFER_DIR = "./temp_buffer"
CLIPS_DIR = "./meus_clipes"
BUFFER_FILE = os.path.join(BUFFER_DIR, "buffer_5min.mp4")

# Flags de controle de threads
rodando = True

def preparar_pastas():
    """Cria as pastas necessárias para o buffer e os clipes salvos."""
    os.makedirs(BUFFER_DIR, exist_ok=True)
    os.makedirs(CLIPS_DIR, exist_ok=True)

def iniciar_buffer_5min(stream_url):
    """
    Roda o FFmpeg em background gravando os últimos 5 minutos (300 segundos)
    de forma circular no arquivo de buffer temporário.
    """
    global rodando
    preparar_pastas()
    
    # Comando FFmpeg:
    # -y: sobrescreve sem pedir
    # -i: URL de entrada do vídeo
    # -c copy: copia o formato nativo sem gastar CPU recodificando
    # -t 300: limita a duração contínua a 300 segundos (5 minutos)
    cmd = [
        "ffmpeg", "-y",
        "-i", stream_url,
        "-c", "copy",
        "-t", "300",
        BUFFER_FILE
    ]

    print("🟢 [Buffer] Iniciando gravação em segundo plano...")
    
    # Executa o processo do FFmpeg
    processo = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    while rodando:
        # Se o processo terminar por limite de tempo, reinicia o loop do buffer
        if processo.poll() is not None:
            processo = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)

    # Finaliza o processo ao fechar o app
    processo.terminate()
    print("🔴 [Buffer] Gravação encerrada.")

def salvar_clipe():
    """Copia o buffer atual de 5 minutos para a pasta de clipes salvos."""
    if not os.path.exists(BUFFER_FILE) or os.path.getsize(BUFFER_FILE) == 0:
        print("\n⚠️ [Erro] O buffer ainda está sendo gerado. Aguarde alguns segundos...")
        return

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_clipe = f"Clipe_Twitch_{timestamp}.mp4"
    caminho_destino = os.path.join(CLIPS_DIR, nome_clipe)

    try:
        # Faz a cópia instantânea do arquivo de buffer sem pausar a gravação
        shutil.copy(BUFFER_FILE, caminho_destino)
        print(f"\n✅ [Sucesso] Clipe de 5 minutos salvo em: {caminho_destino}")
    except Exception as e:
        print(f"\n❌ [Erro ao salvar clipe]: {e}")

# ==========================================
# SIMULAÇÃO DA INTERFACE DO APP (MAIN)
# ==========================================
if __name__ == "__main__":
    preparar_pastas()

    # 1. Inicia a Thread do Buffer (Segunda tarefa em paralelo)
    thread_buffer = threading.Thread(target=iniciar_buffer_5min, args=(STREAM_URL,), daemon=True)
    thread_buffer.start()

    print("\n==============================================")
    print(" 🎬 Player da Live Ativo (Assistindo...) ")
    print("==============================================")
    print(" Digite 'c' para SALVAR OS ÚLTIMOS 5 MINUTOS")
    print(" Digite 's' para SAIR")
    print("==============================================\n")

    # 2. Thread Principal (Menu interativo / Botões da tela)
    try:
        while True:
            opcao = input("Ação [c = Clipar / s = Sair]: ").strip().lower()
            if opcao == 'c':
                salvar_clipe()
            elif opcao == 's':
                print("Encerrando aplicativo...")
                rodando = False
                break
    except KeyboardInterrupt:
        rodando = False

