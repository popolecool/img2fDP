from PIL import Image
import argparse
import os

def compress_hex_line(hex_line):
    compressed = []
    count = 1
    for i in range(1, len(hex_line)):
        if hex_line[i] == hex_line[i-1]:
            count += 1
        else:
            compressed.append(f"{count}x{hex_line[i-1]}")
            count = 1
    compressed.append(f"{count}x{hex_line[-1]}")
    return " ".join(compressed)

def decompress_hex_line(compressed_line):
    decompressed = []
    tokens = compressed_line.strip().split(" ")
    for token in tokens:
        if "x" in token:
            count, value = token.split("x")
            decompressed.extend([value] * int(count))
        else:
            decompressed.append(token)
    return decompressed

def image_to_hex(image_path, output_file, compress=False):
    img = Image.open(image_path)
    img = img.convert("RGB")
    width, height = img.size
    
    with open(output_file, "w") as f:
        for y in range(height):
            hex_line = []
            for x in range(width):
                r, g, b = img.getpixel((x, y))
                hex_value = f"{r:02X}{g:02X}{b:02X}"
                hex_line.append(hex_value)
            
            if compress:
                f.write(compress_hex_line(hex_line) + "\n")
            else:
                f.write(" ".join(hex_line) + "\n")
    print(f"Conversion terminée. '{output_file}'.")

def hex_to_image(input_file, output_file=None, return_image=False):
    with open(input_file, 'r') as f:
        hex_data = f.readlines()

    # Vérifier si compressé
    first_line = hex_data[0].strip()
    is_compressed = "x" in first_line # reged si il y a un x pour savoir si le fichier est compressé

    if is_compressed:
        decompressed_data = []
        for line in hex_data:
            decompressed_data.append(decompress_hex_line(line))
        hex_data = [" ".join(line) for line in decompressed_data]

    height = len(hex_data)
    width = len(hex_data[0].strip().split())

    img = Image.new('RGB', (width, height))
    pixels = img.load()

    for y in range(height):
        hex_values = hex_data[y].strip().split()
        for x in range(width):
            hex_color = hex_values[x]
            r = int(hex_color[0:2], 16) # la valeur hexadécimale de R
            g = int(hex_color[2:4], 16) # la valeur hexadécimale de G
            b = int(hex_color[4:6], 16) # la valeur hexadécimale de B
            pixels[x, y] = (r, g, b)

    if return_image:
        return img  # Retourne l'objet Image directement
    elif output_file:
        img.save(output_file)
        return output_file
    return None

def main():
    parser = argparse.ArgumentParser(description='Convertir entre image et format FDP (Fichier Déjà Parfait)')
    parser.add_argument('-i', '--input', required=True, help="Chemin du fichier d'entrée")
    parser.add_argument('-c', '--compress', action='store_true', help='Activer la compression RLE')
    args = parser.parse_args()

    input_path = args.input
    filename, ext = os.path.splitext(input_path)

    if ext.lower() == '.fdp':
        output_path = filename + '.jpg'
        hex_to_image(input_path, output_path)
    else:
        output_path = filename + '.fdp'
        image_to_hex(input_path, output_path, compress=args.compress)

if __name__ == "__main__":
    main()