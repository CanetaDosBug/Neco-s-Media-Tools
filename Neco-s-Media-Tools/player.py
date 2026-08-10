"""
player.py
Responsável por tocar arquivos locais: áudio via pygame,
vídeo abrindo no player padrão do sistema operacional.
Não sabe nada sobre interface gráfica.
"""

import os
import platform
import subprocess
import pygame


class MediaPlayer:
    """Encapsula a reprodução de arquivos de áudio/vídeo locais."""

    def __init__(self):
        pygame.mixer.init()

    def tocar_audio(self, caminho):
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.play()

    def parar_audio(self):
        pygame.mixer.music.stop()

    def abrir_video_no_player_padrao(self, caminho):
        if not os.path.exists(caminho):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

        sistema = platform.system()
        if sistema == "Windows":
            os.startfile(caminho)
        elif sistema == "Darwin":
            subprocess.run(["open", caminho])
        else:
            subprocess.run(["xdg-open", caminho])
