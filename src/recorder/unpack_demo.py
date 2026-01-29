import sys
import zstandard as zstd

def decompress_demo(input_path, output_path):
    print(f"Decompressing {input_path} to {output_path}...")
    dctx = zstd.ZstdDecompressor()
    with open(input_path, 'rb') as ifh, open(output_path, 'wb') as ofh:
        try:
            dctx.copy_stream(ifh, ofh)
            print("Decompression complete.")
        except zstd.ZstdError as e:
            print(f"Error decompressing: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python unpack_demo.py <input.dem.zst> <output.dem>")
        sys.exit(1)
    
    decompress_demo(sys.argv[1], sys.argv[2])
