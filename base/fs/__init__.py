

def load_volume(data):
	from common.fs.loopbackvolume import LoopbackVolume
	from providers.ec2.ebsvolume import EBSVolume
	from providers.virtualbox.volume import VirtualBoxVolume
	from partitionmaps.gpt import GPTPartitionMap
	from partitionmaps.mbr import MBRPartitionMap
	from partitionmaps.none import NoPartitions
	partition_maps = {'none': NoPartitions,
	                  'gpt': GPTPartitionMap,
	                  'mbr': MBRPartitionMap,
	                  }
	partition_map = partition_maps.get(data['partitions']['type'])(data['partitions'])
	volume_backings = {'raw': LoopbackVolume,
	                   'vdi': VirtualBoxVolume,
	                   'ebs': EBSVolume
	                   }
	return volume_backings.get(data['backing'])(partition_map)
