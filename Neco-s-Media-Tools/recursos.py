"""
recursos.py
Resolve caminhos de arquivos (ícones, ffmpeg, etc.) de um jeito que funciona
tanto rodando com 'python main.py' quanto já compilado com PyInstaller.

Por quê isso é necessário: quando o PyInstaller empacota o programa num .exe,
ele descompacta os arquivos extras (como a pasta assets/) numa pasta
temporária diferente da pasta onde o .py originalmente estava. O PyInstaller
guarda o caminho dessa pasta temporária em sys._MEIPASS. Em modo
desenvolvimento (rodando direto com python), essa variável não existe, então
usamos a pasta atual do projeto mesmo.
"""

import os
import sys


def caminho_recurso(caminho_relativo):
    """
    Recebe um caminho relativo (ex: 'assets/ffmpeg.exe') e devolve o caminho
    absoluto correto, seja rodando via python ou já compilado.
    """
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, caminho_relativo)


def caminho_ffmpeg_embutido():
    """
    Resolve o caminho do ffmpeg embutido em assets/, usando o nome certo
    conforme o sistema operacional: no Windows, o executável se chama
    'ffmpeg.exe'; no Linux e no Mac, o nome é só 'ffmpeg', sem extensão
    nenhuma no final.

    Retorna None se o arquivo não existir (por exemplo, se você ainda não
    colocou o ffmpeg dentro de assets/). Quem chamar essa função deve tratar
    esse None como "usa o ffmpeg que já está instalado no sistema".
    """
    nome_executavel = "ffmpeg.exe" if sys.platform.startswith("win") else "ffmpeg"
    caminho = caminho_recurso(os.path.join("assets", nome_executavel))
    return caminho if os.path.exists(caminho) else None
