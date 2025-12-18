from typing import Dict, List, Tuple, Optional
import os
from .mts_parser import MTSParser


class MTSAnalyzer:
    @staticmethod
    def get_statistics(filepath: str) -> Dict:
        metadata = MTSParser.get_metadata(filepath)
        file_size = os.path.getsize(filepath)

        stats = {'file_info': {
            'path': filepath,
            'size_bytes': file_size,
            'size_human': MTSAnalyzer._format_size(file_size),
        }, 'schematic_info': {
            'version': metadata['header']['version'],
            'dimensions': (metadata['header']['width'],
                           metadata['header']['height'],
                           metadata['header']['length']),
            'volume': metadata['header']['volume'],
            'volume_human': MTSAnalyzer._format_number(metadata['header']['volume']),
        }, 'composition': {
            'node_types': metadata['nodelist']['count'],
            'has_air': metadata['nodelist']['has_air'],
            'yprobs_present': metadata['yprobs']['count'] > 0,
            'yprobs_count': metadata['yprobs']['count'],
        }, 'compression': {
            'compressed_size': metadata['data_section']['compressed_size'],
            'estimated_uncompressed': metadata['data_section']['uncompressed_size_estimate'],
            'compression_ratio': round(
                metadata['data_section']['compressed_size'] /
                metadata['data_section']['uncompressed_size_estimate'], 2
            ) if metadata['data_section']['uncompressed_size_estimate'] > 0 else 0,
        }, 'estimated_density': MTSAnalyzer._estimate_density(metadata)}

        # Calculate density (non-air percentage if we had the data)
        # This is an estimate based on common patterns

        return stats

    @staticmethod
    def compare_files(file1: str, file2: str) -> Dict:
        stats1 = MTSAnalyzer.get_statistics(file1)
        stats2 = MTSAnalyzer.get_statistics(file2)

        comparison = {
            'dimensions_match': (
                    stats1['schematic_info']['dimensions'] ==
                    stats2['schematic_info']['dimensions']
            ),
            'volume_difference': abs(
                stats1['schematic_info']['volume'] -
                stats2['schematic_info']['volume']
            ),
            'size_ratio': round(
                stats1['file_info']['size_bytes'] /
                stats2['file_info']['size_bytes'], 2
            ),
            'compression_ratio_difference': abs(
                stats1['compression']['compression_ratio'] -
                stats2['compression']['compression_ratio']
            ),
        }

        return {
            'file1_stats': stats1,
            'file2_stats': stats2,
            'comparison': comparison
        }

    @staticmethod
    def find_common_nodes(filepaths: List[str]) -> Dict:
        all_nodes = []
        node_sets = []

        for filepath in filepaths:
            metadata = MTSParser.get_metadata(filepath)
            nodes = set(metadata['nodelist']['nodes'])
            all_nodes.extend(nodes)
            node_sets.append(nodes)

        # Find intersection (nodes in all files)
        common_nodes = set.intersection(*node_sets) if node_sets else set()

        # Find unique nodes per file
        unique_per_file = []
        for i, node_set in enumerate(node_sets):
            other_sets = node_sets[:i] + node_sets[i + 1:]
            other_union = set.union(*other_sets) if other_sets else set()
            unique = node_set - other_union
            unique_per_file.append({
                'file': filepaths[i],
                'unique_nodes': list(unique),
                'count': len(unique)
            })

        return {
            'total_files': len(filepaths),
            'total_unique_nodes': len(set(all_nodes)),
            'common_nodes': {
                'nodes': list(common_nodes),
                'count': len(common_nodes)
            },
            'unique_nodes_per_file': unique_per_file
        }

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    @staticmethod
    def _format_number(number: int) -> str:
        """Format large numbers with commas."""
        return f"{number:,}"

    @staticmethod
    def _estimate_density(metadata: Dict) -> float:
        compression_ratio = (
            metadata['data_section']['compressed_size'] /
            metadata['data_section']['uncompressed_size_estimate']
            if metadata['data_section']['uncompressed_size_estimate'] > 0 else 1.0
        )

        # Lower compression ratio usually means more repetition (air)
        # Higher compression ratio means more unique data
        if compression_ratio < 0.1:
            return 10.0  # Very sparse
        elif compression_ratio < 0.3:
            return 30.0  # Sparse
        elif compression_ratio < 0.6:
            return 60.0  # Medium
        elif compression_ratio < 0.8:
            return 80.0  # Dense
        else:
            return 95.0  # Very dense

