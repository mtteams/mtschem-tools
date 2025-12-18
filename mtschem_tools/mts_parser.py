import struct
import zlib
from typing import Dict, Tuple, List, Optional, BinaryIO
import io


class MTSParser:
    @staticmethod
    def parse_header(filepath: str) -> Dict:
        with open(filepath, 'rb') as f:
            # Read signature (4 bytes)
            signature = f.read(4)

            # Read version (2 bytes, big-endian)
            version_bytes = f.read(2)
            version = struct.unpack('>H', version_bytes)[0] if len(version_bytes) == 2 else 0

            # Read dimensions (3 x 2 bytes, big-endian)
            dim_bytes = f.read(6)
            if len(dim_bytes) == 6:
                width, height, length = struct.unpack('>HHH', dim_bytes)
            else:
                width = height = length = 0

            # Calculate volume
            volume = width * height * length

            return {
                'signature': signature,
                'signature_valid': signature == b'MTSM',
                'version': version,
                'width': width,
                'height': height,
                'length': length,
                'volume': volume,
                'file_size': f.tell()  # Current position after header
            }

    @staticmethod
    def parse_yprobs(filepath: str) -> Tuple[List[int], int]:
        header = MTSParser.parse_header(filepath)
        yprobs_size = header['height']

        with open(filepath, 'rb') as f:
            # Skip to yprobs section (4 + 2 + 6 bytes)
            f.seek(12)

            # Read yprobs
            yprobs_data = f.read(yprobs_size)
            yprobs = list(yprobs_data) if len(yprobs_data) == yprobs_size else []

            return yprobs, f.tell()

    @staticmethod
    def parse_nodelist(filepath: str) -> Tuple[List[str], int]:
        header = MTSParser.parse_header(filepath)

        with open(filepath, 'rb') as f:
            # Skip to nodelist section (header + yprobs)
            f.seek(12 + header['height'])

            # Read node count (2 bytes, big-endian)
            nodecount_bytes = f.read(2)
            if len(nodecount_bytes) != 2:
                return [], f.tell()

            nodecount = struct.unpack('>H', nodecount_bytes)[0]
            nodes = []

            # Read each node name
            for _ in range(nodecount):
                # Read name length (2 bytes, big-endian)
                namelen_bytes = f.read(2)
                if len(namelen_bytes) != 2:
                    break

                namelen = struct.unpack('>H', namelen_bytes)[0]

                # Read node name
                name_bytes = f.read(namelen)
                if len(name_bytes) != namelen:
                    break

                nodes.append(name_bytes.decode('utf-8', errors='ignore'))

            return nodes, f.tell()

    @staticmethod
    def get_metadata(filepath: str) -> Dict:
        header = MTSParser.parse_header(filepath)
        yprobs, ypos = MTSParser.parse_yprobs(filepath)
        nodes, npos = MTSParser.parse_nodelist(filepath)

        # Get compressed data size
        import os
        file_size = os.path.getsize(filepath)
        compressed_size = file_size - npos

        return {
            'header': header,
            'yprobs': {
                'values': yprobs,
                'count': len(yprobs),
                'expected': header['height']
            },
            'nodelist': {
                'nodes': nodes,
                'count': len(nodes),
                'has_air': 'air' in nodes if nodes else False
            },
            'data_section': {
                'offset': npos,
                'compressed_size': compressed_size,
                'uncompressed_size_estimate': header['volume'] * 4  # node(2) + prob/force(1) + param2(1)
            }
        }

    @staticmethod
    def extract_compressed_data(filepath: str, output_file: Optional[str] = None) -> bytes:
        metadata = MTSParser.get_metadata(filepath)
        data_offset = metadata['data_section']['offset']

        with open(filepath, 'rb') as f:
            f.seek(data_offset)
            compressed_data = f.read()

        if output_file:
            with open(output_file, 'wb') as f:
                f.write(compressed_data)

        return compressed_data

    @staticmethod
    def decompress_bulk_data(compressed_data: bytes) -> Optional[bytes]:
        try:
            return zlib.decompress(compressed_data)
        except zlib.error as e:
            print(f"Decompression error: {e}")
            return None