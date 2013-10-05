from abstract import AbstractPartitionMap
from ..partitions.gpt import GPTPartition
from ..partitions.gpt_swap import GPTSwapPartition
from common.tools import log_check_call


class GPTPartitionMap(AbstractPartitionMap):

	def __init__(self, data):
		self.partitions = []
		if 'boot' in data:
			self.boot = GPTPartition(data['boot']['size'], data['boot']['filesystem'], 'boot', None)
			self.partitions.append(self.boot)
		self.root = GPTPartition(data['root']['size'], data['root']['filesystem'], 'root', self.boot)
		self.partitions.append(self.root)
		if 'swap' in data:
			self.swap = GPTSwapPartition(data['swap']['size'], self.root)
			self.partitions.append(self.swap)

		super(GPTPartitionMap, self).__init__()

	def _before_create(self, event):
		volume = event.volume
		log_check_call(['/sbin/parted', '--script', '--align', 'none', volume.device_path,
		                '--', 'mklabel', 'gpt'])
		for partition in self.partitions:
			partition.create(volume)

		boot_idx = self.root.get_index()
		if hasattr(self, 'boot'):
			boot_idx = self.boot.get_index()
		log_check_call(['/sbin/parted', '--script', volume.device_path,
		                '--', 'set ' + str(boot_idx) + ' boot on'])
		log_check_call(['/sbin/parted', '--script', volume.device_path,
		                '--', 'set ' + str(boot_idx) + ' bios_grub on'])
