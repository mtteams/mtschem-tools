"""
Text-based visualization utilities for .mts files.
"""

from typing import List, Tuple, Optional
from .mts_parser import MTSParser


class MTSVisualizer:
    @staticmethod
    def get_ascii_slice(filepath: str, axis: str = 'z',
                        slice_index: int = 0,
                        max_width: int = 80) -> str:

        metadata = MTSParser.get_metadata(filepath)
        nodes = metadata['nodelist']['nodes']

        width, height, length = metadata['header']['width'], \
            metadata['header']['height'], \
            metadata['header']['length']

        # Determine slice dimensions
        if axis == 'x':
            if slice_index >= width:
                return f"Slice index {slice_index} out of range (width={width})"
            slice_dims = (height, length)
        elif axis == 'y':
            if slice_index >= height:
                return f"Slice index {slice_index} out of range (height={height})"
            slice_dims = (width, length)
        else:  # axis == 'z'
            if slice_index >= length:
                return f"Slice index {slice_index} out of range (length={length})"
            slice_dims = (width, height)

        # Create placeholder ASCII (since we don't have actual block data)
        ascii_chars = " .:ioOC@#"  # Darkness scale

        # Calculate scaling if needed
        output_width = min(slice_dims[0], max_width)
        scale_x = slice_dims[0] / output_width if slice_dims[0] > output_width else 1

        # Build ASCII representation
        result = []
        result.append(f"Slice {axis}={slice_index} ({slice_dims[0]}x{slice_dims[1]})")
        result.append("=" * min(80, slice_dims[0]))

        # Simplified representation
        # In a real implementation, you would need the actual block data
        for y in range(min(20, slice_dims[1])):  # Limit height for display
            line = []
            for x in range(min(output_width, slice_dims[0])):
                # Placeholder: use position to determine character
                char_idx = (x + y) % len(ascii_chars)
                line.append(ascii_chars[char_idx])
            result.append(''.join(line))

        if slice_dims[1] > 20:
            result.append(f"... ({slice_dims[1] - 20} more rows)")

        return '\n'.join(result)

    @staticmethod
    def get_text_summary(filepath: str, detailed: bool = False) -> str:
        metadata = MTSParser.get_metadata(filepath)

        summary = []
        summary.append(f"MTS File: {filepath}")
        summary.append("=" * 50)

        # Basic info
        header = metadata['header']
        summary.append(f"Version: {header['version']}")
        summary.append(f"Dimensions: {header['width']}x{header['height']}x{header['length']}")
        summary.append(f"Volume: {header['volume']:,} blocks")

        # Node list
        nodelist = metadata['nodelist']
        summary.append(f"Node types: {nodelist['count']}")

        if detailed and nodelist['nodes']:
            summary.append("\nNodes:")
            for i, node in enumerate(nodelist['nodes'][:10]):  # First 10
                summary.append(f"  {i:3d}: {node}")
            if len(nodelist['nodes']) > 10:
                summary.append(f"  ... and {len(nodelist['nodes']) - 10} more")

        # Y-probs
        yprobs = metadata['yprobs']
        if yprobs['count'] > 0:
            unique_probs = len(set(yprobs['values']))
            summary.append(f"Y-probabilities: {yprobs['count']} values ({unique_probs} unique)")

        data_section = metadata['data_section']
        comp_ratio = data_section['compressed_size'] / data_section['uncompressed_size_estimate'] \
            if data_section['uncompressed_size_estimate'] > 0 else 0

        summary.append(f"\nCompression:")
        summary.append(f"  Compressed: {data_section['compressed_size']:,} bytes")
        summary.append(f"  Estimated uncompressed: {data_section['uncompressed_size_estimate']:,} bytes")
        summary.append(f"  Ratio: {comp_ratio:.2%}")

        return '\n'.join(summary)

    @staticmethod
    def create_block_diagram(filepath: str) -> str:
        metadata = MTSParser.get_metadata(filepath)
        width, height, length = metadata['header']['width'], \
            metadata['header']['height'], \
            metadata['header']['length']

        max_dim = max(width, height, length)
        scale = 20 / max_dim if max_dim > 20 else 1

        diagram = []
        diagram.append("Schematic Block Diagram")
        diagram.append("=" * 30)

        diagram.append("\nTop View (X-Z plane):")
        scaled_width = int(width * scale)
        scaled_length = int(length * scale)

        for z in range(scaled_length):
            line = []
            for x in range(scaled_width):
                line.append('#')
            diagram.append(''.join(line))

        diagram.append("\nFront View (X-Y plane):")
        scaled_height = int(height * scale)

        for y in range(scaled_height - 1, -1, -1):  # Draw from top to bottom
            line = []
            for x in range(scaled_width):
                line.append('#')
            diagram.append(''.join(line))

        diagram.append(f"\nDimensions: {width}W × {height}H × {length}L")
        diagram.append(f"(Diagram scaled {scale:.2f}x)")

        return '\n'.join(diagram)
