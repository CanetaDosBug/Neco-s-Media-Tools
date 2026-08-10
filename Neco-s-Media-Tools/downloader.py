"""
downloader.py
Responsável por toda a lógica de download com yt-dlp.
Não sabe nada sobre interface gráfica.
"""

import os
import yt_dlp


class MediaDownloader:
    """Encapsula a lógica de download de áudio/vídeo via yt-dlp."""

    FORMATOS = {
        "MP3 (áudio)":  ("mp3",  True),
        "WAV (áudio)":  ("wav",  True),
        "M4A (áudio)":  ("m4a",  True),
        "FLAC (áudio)": ("flac", True),
        "OPUS (áudio)": ("opus", True),
        "MP4 (vídeo)":  ("mp4",  False),
        "WEBM (vídeo)": ("webm", False),
        "MKV (vídeo)":  ("mkv",  False),
    }

    def __init__(self, ffmpeg_location=None):
        # Se o ffmpeg não estiver no PATH, passe o caminho aqui.
        self.ffmpeg_location = ffmpeg_location

    def formatos_disponiveis(self):
        """Retorna os nomes exibidos no seletor de formato."""
        return list(self.FORMATOS.keys())

    def is_audio(self, nome_formato):
        return self.FORMATOS[nome_formato][1]

    def _montar_opcoes(self, destino, nome_formato, progress_callback):
        extensao, e_audio = self.FORMATOS[nome_formato]

        opcoes = {
            'outtmpl': os.path.join(destino, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_callback] if progress_callback else [],
        }

        if self.ffmpeg_location:
            opcoes['ffmpeg_location'] = self.ffmpeg_location

        if e_audio:
            opcoes['format'] = 'bestaudio/best'
            opcoes['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': extensao,
                'preferredquality': '192',
            }]
        else:
            opcoes['format'] = 'bestvideo+bestaudio/best'
            opcoes['merge_output_format'] = extensao

        return opcoes, extensao

    def baixar(self, url, destino, nome_formato, progress_callback=None):
        """
        Baixa o conteúdo da URL no formato escolhido.
        Retorna o caminho final do arquivo baixado.
        """
        opcoes, extensao = self._montar_opcoes(destino, nome_formato, progress_callback)

        with yt_dlp.YoutubeDL(opcoes) as ydl:
            info = ydl.extract_info(url, download=True)
            nome_base = ydl.prepare_filename(info)

        caminho_final = os.path.splitext(nome_base)[0] + f".{extensao}"

        if os.path.exists(caminho_final):
            return caminho_final
        return nome_base  # fallback, caso a extensão final seja diferente
