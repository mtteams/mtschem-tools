"""
Generators for creating simple .mts files.
"""

import struct
import zlib
from typing import List, Tuple, Optional, Dict
import io


class MTSGenerator:
    @staticmethod
    def create_empty_schematic(width: int, height: int, length: int,
                               version: int = 4) -> bytes:
        # Validate dimensions
        if width <= 0 or height <= 0 or length <= 0:
            raise ValueError("Dimensions must be positive")
        if width > 65535 or height > 65535 or length > 65535:
            raise ValueError("Dimensions cannot exceed 65535")

        # Calculate volume
        volume = width * height * length

        # Create header
        output = io.BytesIO()

        # Signature
        output.write(b'MTSM')

        # Version
        output.write(struct.pack('>H', version))

        # Dimensions
        output.write(struct.pack('>HHH', width, height, length))

        # Y-probabilities (all 127 = always generate)
        output.write(bytes([127] * height))

        # Node list (only air)
        output.write(struct.pack('>H', 1))  # 1 node
        output.write(struct.pack('>H', 3))  # "air" length = 3
        output.write(b'air')

        # Bulk data
        bulk_data = io.BytesIO()

        # Node IDs (all 0 = air)
        bulk_data.write(b'\x00\x00' * volume)

        # Prob/Force bytes (all 0)
        bulk_data.write(b'\x00' * volume)

        # Param2 bytes (all 0)
        bulk_data.write(b'\x00' * volume)

        # Compress bulk data
        compressed = zlib.compress(bulk_data.getvalue(), level=9)
        output.write(compressed)

        return output.getvalue()

    @staticmethod
    def create_box(width: int, height: int, length: int,
                   wall_block: str = "default:stone",
                   fill_block: Optional[str] = None,
                   hollow: bool = True) -> bytes:

        # Create empty schematic first
        schematic = MTSGenerator.create_empty_schematic(width, height, length)

        # For now, return the empty schematic
        # TODO: Implement block replacement logic

        return schematic

    @staticmethod
    def create_from_template(template: Dict) -> bytes:
        # Extract parameters
        dimensions = template.get('dimensions', (1, 1, 1))
        nodes = template.get('nodes', ['air'])
        data = template.get('data', [])

        width, height, length = dimensions
        volume = width * height * length

        # Create output buffer
        output = io.BytesIO()

        # Write header
        output.write(b'MTSM')
        output.write(struct.pack('>H', 4))  # Version

        # Write dimensions
        output.write(struct.pack('>HHH', width, height, length))

        # Write yprobs (all 127)
        output.write(bytes([127] * height))

        # Write node list
        output.write(struct.pack('>H', len(nodes)))
        for node in nodes:
            name_bytes = node.encode('utf-8')
            output.write(struct.pack('>H', len(name_bytes)))
            output.write(name_bytes)

        # Create bulk data
        bulk_data = io.BytesIO()

        # Default: all air
        if not data:
            # Node IDs (all 0 = air)
            bulk_data.write(b'\x00\x00' * volume)
            # Prob/Force (all 0)
            bulk_data.write(b'\x00' * volume)
            # Param2 (all 0)
            bulk_data.write(b'\x00' * volume)
        else:
            # TODO: Implement data population from template
            # This would require converting template data to MTS format
            pass

        # Compress and write bulk data
        compressed = zlib.compress(bulk_data.getvalue(), level=6)
        output.write(compressed)

        return output.getvalue()
