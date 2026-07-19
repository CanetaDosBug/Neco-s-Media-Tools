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
