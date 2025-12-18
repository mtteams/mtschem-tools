import os
from typing import Tuple, List, Dict
import struct


class MTSValidator:
    @staticmethod
    def validate_file(filepath: str) -> Tuple[bool, List[str], Dict]:
        errors = []
        metadata = {}

        # Check file existence
        if not os.path.exists(filepath):
            errors.append(f"File does not exist: {filepath}")
            return False, errors, metadata

        # Check file size
        file_size = os.path.getsize(filepath)
        if file_size < 20:
            errors.append(f"File too small ({file_size} bytes). Minimum MTS size is 20 bytes.")
            return False, errors, metadata

        # Check file extension
        if not filepath.lower().endswith('.mts'):
            errors.append("File extension is not .mts")

        try:
            with open(filepath, 'rb') as f:
                # Check signature
                signature = f.read(4)
                if signature != b'MTSM':
                    errors.append(f"Invalid signature: {signature.hex()}")

                # Check version
                version_bytes = f.read(2)
                if len(version_bytes) != 2:
                    errors.append("Cannot read version")
                else:
                    version = struct.unpack('>H', version_bytes)[0]
                    metadata['version'] = version
                    if version not in [3, 4, 5]:
                        errors.append(f"Unsupported version: {version}")

                # Check dimensions
                dim_bytes = f.read(6)
                if len(dim_bytes) != 6:
                    errors.append("Cannot read dimensions")
                else:
                    width, height, length = struct.unpack('>HHH', dim_bytes)
                    metadata['dimensions'] = (width, height, length)
                    metadata['volume'] = width * height * length

                    # Validate dimensions
                    if width == 0 or height == 0 or length == 0:
                        errors.append(f"Invalid dimensions: {width}x{height}x{length}")
                    if width > 65535 or height > 65535 or length > 65535:
                        errors.append(f"Dimensions too large: {width}x{height}x{length}")

                # Check yprobs
                if 'dimensions' in metadata:
                    yprobs_data = f.read(metadata['dimensions'][1])
                    if len(yprobs_data) != metadata['dimensions'][1]:
                        errors.append(f"Incomplete yprobs data: expected {metadata['dimensions'][1]} bytes")
                    else:
                        metadata['yprobs_length'] = len(yprobs_data)

                # Check node count
                nodecount_bytes = f.read(2)
                if len(nodecount_bytes) != 2:
                    errors.append("Cannot read node count")
                else:
                    nodecount = struct.unpack('>H', nodecount_bytes)[0]
                    metadata['node_count'] = nodecount

                # Get position for compressed data size estimation
                current_pos = f.tell()
                compressed_size = file_size - current_pos
                metadata['compressed_data_size'] = compressed_size

                # Estimate uncompressed size
                if 'volume' in metadata:
                    estimated_uncompressed = metadata['volume'] * 4  # 4 bytes per voxel
                    if compressed_size > estimated_uncompressed * 2:
                        errors.append(f"Compressed data too large: {compressed_size} bytes")

        except Exception as e:
            errors.append(f"Error reading file: {str(e)}")

        # Check if file is complete
        if len(errors) == 0 and 'dimensions' in metadata:
            expected_min_size = 12 + metadata['dimensions'][1] + 2  # header + yprobs + nodecount
            if file_size < expected_min_size:
                errors.append(f"File truncated: size {file_size} < minimum {expected_min_size}")

        return len(errors) == 0, errors, metadata

    @staticmethod
    def check_corruption(filepath: str, quick: bool = True) -> Tuple[bool, str]:
        is_valid, errors, _ = MTSValidator.validate_file(filepath)

        if not is_valid:
            return False, f"File invalid: {', '.join(errors)}"

        if not quick:
            # Try to decompress data
            try:
                from .mts_parser import MTSParser
                compressed_data = MTSParser.extract_compressed_data(filepath)
                decompressed = MTSParser.decompress_bulk_data(compressed_data)

                if decompressed is None:
                    return False, "Compressed data cannot be decompressed"

                # Check decompressed size
                metadata = MTSParser.get_metadata(filepath)
                expected_size = metadata['header']['volume'] * 4
                if len(decompressed) != expected_size:
                    return False, f"Decompressed size mismatch: {len(decompressed)} != {expected_size}"

                return True, "File appears healthy (full check)"

            except Exception as e:
                return False, f"Error during full check: {str(e)}"

        return True, "File appears healthy (quick check)"

