import subprocess
import os
import sys

def comprimir_video(input_file, output_file, crf=28):
    """
    Comprime um vídeo usando ffmpeg.
    
    Args:
        input_file (str): Caminho do arquivo de entrada.
        output_file (str): Caminho do arquivo de saída.
        crf (int): Constant Rate Factor (0-51). Menor é melhor qualidade, maior é menor tamanho.
                   23 é o padrão, 28 é uma boa compressão.
    """
    if not os.path.exists(input_file):
        print(f"Erro: Arquivo de entrada '{input_file}' não encontrado.")
        return

    # Comando ffmpeg
    # -i: input
    # -vcodec libx264: codec de vídeo
    # -crf: fator de qualidade
    # -preset faster: velocidade de compressão (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
    command = [
        'ffmpeg',
        '-i', input_file,
        '-vcodec', 'libx264',
        '-crf', str(crf),
        '-preset', 'faster',
        output_file
    ]

    print(f"Iniciando compressão: {input_file} -> {output_file}")
    print(f"Comando: {' '.join(command)}")

    try:
        subprocess.run(command, check=True)
        print("\nCompressão concluída com sucesso!")
        
        # Comparar tamanhos
        original_size = os.path.getsize(input_file) / (1024 * 1024)
        new_size = os.path.getsize(output_file) / (1024 * 1024)
        print(f"Tamanho original: {original_size:.2f} MB")
        print(f"Novo tamanho: {new_size:.2f} MB")
        print(f"Redução: {original_size - new_size:.2f} MB ({(1 - new_size/original_size)*100:.1f}%)")

    except subprocess.CalledProcessError as e:
        print(f"Erro durante a compressão: {e}")
    except FileNotFoundError:
        print("Erro: ffmpeg não encontrado. Certifique-se de que o ffmpeg está instalado e no PATH.")

if __name__ == "__main__":
    arquivo_entrada = "sga.mp4"
    arquivo_saida = "sga_comprimido.mp4"
    
    # Se passar argumentos via linha de comando
    if len(sys.argv) > 1:
        arquivo_entrada = sys.argv[1]
    if len(sys.argv) > 2:
        arquivo_saida = sys.argv[2]

    comprimir_video(arquivo_entrada, arquivo_saida)
