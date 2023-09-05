import os
import shutil
import re
import bencode
import yaml


def load_config():
    with open('config.yaml', 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config


def extract_file_names(torrent_file):
    with open(torrent_file, 'rb') as f:
        data = bencode.bdecode(f.read())

    file_names = []
    if 'info' in data:
        info = data['info']
        if 'files' in info:
            files = info['files']
            for file_info in files:
                if 'path' in file_info:
                    file_name = file_info['path'][-1]
                    if file_name.endswith(('.mkv', '.avi')):
                        file_names.append(file_name)
    return file_names


def clean_filename(filename):
    # Lista de patrones y sus reemplazos correspondientes
    patterns = [
        ('.', ' '),
        ('4k', ''), ('4K', ''),
        ('www atomohd care', ''),
        ('[Wolfmax4k com]', ''), ('[Wolfmax com]', ''), ('(wolfmax com]', ''), ('(wolfmax COM]', ''),
        ('[depechemode13]', ''), ('CartmanGold', ''), ('-Bryan_122', ''), ('yamil', ''),
        (' anos ', ' años '), (' ano ', ' año '),
        ('2032', '2023'),
        ('Caap', 'Cap'),
        ('Castellano', 'Esp'),
        ('DUAL', '[Dual]'),
        ('A3P', '[A3P]'), ('DSNP', '[DSNP]'),
        ('AVC', '[AVC]'), ('H 264', '[H264]'),
        ('AAC 2 0', '[AAC 2.0]'), ('DDP5 1', '[DDP 5.1]'),
        ('720', '[720p]'),
        ('m1080p', '[1080p]'), ('1080', '[1080p]'),
        ('2160', '[2160p]'), ('20160p', '[2160p]'), ('2106p', '[2160p]'), ('2016p', '[2160p]'),
        ('HDTV', '[HDTV]'),
        ('[Blurayrip]', '[Bluray]'), ('Bluray', '[Bluray]'), ('BLuray', '[Bluray]'),
        ('[[Bluray]rip]', '[Bluray]'), (' rip[', ' ['),
        ('WEB-DL', '[WEB-DL]'), ('WEBDL', '[WEB-DL]'),
        (']p]', ']'), ('] [', ']['), ('[ ', '['), ('] ', ']'), ('[[', '['), (']]', ']'), ('pp', ''),
        ('[Bluray][Esp]', '[Bluray][480p][Esp]'),
        ('[HDTV][Cap', '[HDTV][480p][Cap'),
        ('[HDTC][Cap', '[HDTC][480p][Cap'),
    ]

    # Aplicar los patrones de reemplazo en el nombre del archivo
    cleaned_filename = filename
    for pattern, replacement in patterns:
        cleaned_filename = cleaned_filename.replace(pattern, replacement)
    # Eliminar espacios en blanco adicionales al principio y al final
    cleaned_filename = cleaned_filename.strip()
    # Eliminar los paréntesis al principio del nombre del archivo
    cleaned_filename = re.sub(r'^\(([^)]*)\)', '\\1', cleaned_filename)
    # Eliminar el texto entre paréntesis, excepto si contiene números
    cleaned_filename = re.sub(r'\((?!\d+\))[^)]*\)', '', cleaned_filename)
    # Eliminar múltiples espacios en blanco (cualquier tipo) consecutivos y reemplazarlos por un solo espacio
    cleaned_filename = re.sub(r'\s+', ' ', cleaned_filename, flags=re.UNICODE)
    # Eliminar espacios en blanco adicionales entre palabras
    cleaned_filename = ' '.join(cleaned_filename.split())
    # Eliminar el último caracter si es un ']'
    if cleaned_filename.endswith(']['):
        cleaned_filename = cleaned_filename[:-1]
    # Eliminar si el nombre de archivo comienza con '.' o un espacio
    while cleaned_filename.startswith('.') or cleaned_filename.startswith(' '):
        cleaned_filename = cleaned_filename[1:]
    # Eliminar lo que viene despues de [esp]
    esp_index = cleaned_filename.find('[Esp]')
    if esp_index != -1:
        cleaned_filename = cleaned_filename[:esp_index + 5]
    return cleaned_filename


def rename_and_copy_torrents(source_folder, dest_folder, torrents_filename, media_filename):
    # Verificar si la carpeta de destino ya existe
    if os.path.exists(dest_folder):
        # Eliminar la carpeta de destino y su contenido de forma recursiva
        shutil.rmtree(dest_folder)
        print(f"Se ha eliminado la carpeta de destino existente: {dest_folder}")

    # Crear la carpeta de destino nuevamente
    os.makedirs(dest_folder)
    print(f"Se ha creado la carpeta de destino: {dest_folder}")

    # Listas para almacenar los nombres de los archivos .torrent sin la extensión,
    # y los nombres de los archivos .mkv y .avi originales
    torrent_names = []
    media_files = []

    # Recorrer los archivos de la carpeta de origen y sus subdirectorios
    for root, _, files in os.walk(source_folder):
        for torrent_file in files:
            # Procesar solo los archivos con extensión .torrent
            if torrent_file.endswith('.torrent'):
                torrent_path = os.path.join(root, torrent_file)
                file_names = extract_file_names(torrent_path)

                if file_names:
                    if len(file_names) == 1:
                        original_filename = os.path.splitext(file_names[0])[0]
                        new_torrent_name = clean_filename(original_filename)
                        new_torrent_path = os.path.join(dest_folder, new_torrent_name + '.torrent')
                        # Copiar el archivo .torrent renombrado a la carpeta de destino
                        shutil.copy2(torrent_path, new_torrent_path)
                        print(
                            f"Se ha copiado el archivo {torrent_file} como {new_torrent_name}.torrent"
                            f" en la carpeta de destino.")

                        # Agregar el nombre limpio del archivo .torrent (sin la extensión) a la lista
                        torrent_names.append(new_torrent_name)

                        # Guardar los nombres de los archivos .mkv y .avi originales
                        if file_names[0].lower().endswith(('.mkv', '.avi')):
                            media_files.append(file_names[0])
                    else:
                        print(f"Se encontraron varios archivos .mkv o .avi en {torrent_file} "
                              f"No se puede determinar el nombre del nuevo archivo .torrent")

    # Ruta donde se encuentra el programa Python
    program_dir = os.path.dirname(os.path.abspath(__file__))

    # Escribir los nombres de los archivos .torrent (sin la extensión) en el archivo torrents_filename
    with open(os.path.join(program_dir, f'{torrents_filename}'), 'w', encoding='ISO-8859-1') as torrents_file:
        for torrent_name in torrent_names:
            torrents_file.write(torrent_name + '\n')

    print(
        f"Se ha creado el archivo {torrents_filename} en la ruta del script.")

    # Escribir los nombres de los archivos .mkv y .avi originales en el archivo media_filename
    with open(os.path.join(program_dir, f'{media_filename}'), 'w', encoding='ISO-8859-1') as media_file:
        for media_name in media_files:
            media_file.write(media_name + '\n')

    print(f"Se ha creado el archivo {media_filename} la ruta del script.")


def main():
    config = load_config()
    source_folder = config['source_folder']
    dest_folder = config['dest_folder']
    torrents_filename = config['torrents_filename']
    media_filename = config['media_filename']

    rename_and_copy_torrents(source_folder, dest_folder, torrents_filename, media_filename)


if __name__ == "__main__":
    main()
