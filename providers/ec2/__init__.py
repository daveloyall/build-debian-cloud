from manifest import Manifest
import logging
from tasks import packages
from common.tasks import packages as common_packages
from tasks import connection
from tasks import host
from common.tasks import host as common_host
from tasks import ami
from common.tasks import volume
from tasks import ebs
from common.tasks import loopback
from common.tasks import filesystem
from common.tasks import bootstrap
from common.tasks import locale
from common.tasks import apt
from tasks import boot
from common.tasks import boot as common_boot
from common.tasks import security
from tasks import network
from common.tasks import network as common_network
from tasks import initd
from common.tasks import initd as common_initd
from common.tasks import cleanup


def initialize():
	# Regardless of of loglevel, we don't want boto debug stuff, it's very noisy
	logging.getLogger('boto').setLevel(logging.INFO)


def tasks(tasklist, manifest):
	tasklist.add(packages.HostPackages(),
	             common_packages.HostPackages(),
	             packages.ImagePackages(),
	             common_packages.ImagePackages(),
	             common_host.CheckPackages(),
	             connection.GetCredentials(),
	             host.GetInfo(),
	             ami.AMIName(),
	             connection.Connect(),

	             filesystem.FormatVolume(),
	             filesystem.CreateMountDir(),
	             filesystem.MountVolume(),

	             bootstrap.Bootstrap(),
	             filesystem.MountSpecials(),
	             locale.GenerateLocale(),
	             locale.SetTimezone(),
	             apt.DisableDaemonAutostart(),
	             apt.AptSources(),
	             apt.AptUpgrade(),
	             boot.ConfigureGrub(),
	             filesystem.FStab(),
	             common_boot.BlackListModules(),
	             common_boot.DisableGetTTYs(),
	             security.EnableShadowConfig(),
	             security.DisableSSHPasswordAuthentication(),
	             security.DisableSSHDNSLookup(),
	             common_network.RemoveDNSInfo(),
	             common_network.ConfigureNetworkIF(),
	             network.EnableDHCPCDDNS(),
	             common_initd.ResolveInitScripts(),
	             initd.AddEC2InitScripts(),
	             common_initd.InstallInitScripts(),
	             cleanup.ClearMOTD(),
	             cleanup.ShredHostkeys(),
	             cleanup.CleanTMP(),
	             apt.PurgeUnusedPackages(),
	             apt.AptClean(),
	             apt.EnableDaemonAutostart(),
	             filesystem.UnmountSpecials(),

	             filesystem.UnmountVolume(),
	             filesystem.DeleteMountDir(),
	             ami.RegisterAMI())

	if manifest.bootstrapper.get('tarball', False):
		tasklist.add(bootstrap.MakeTarball())

	backing_specific_tasks = {'ebs': [ebs.Create(),
	                                  volume.Attach(),
	                                  volume.Detach(),
	                                  ebs.Snapshot(),
	                                  volume.Delete()],
	                          's3': [loopback.Create(),
	                                 volume.Attach(),
	                                 volume.Detach(),
	                                 ami.BundleImage(),
	                                 ami.UploadImage(),
	                                 volume.Delete(),
	                                 ami.RemoveBundle()]}
	tasklist.add(*backing_specific_tasks.get(manifest.volume['backing'].lower()))

	filesystem_specific_tasks = {'xfs': [filesystem.AddXFSProgs()],
	                             'ext2': [filesystem.TuneVolumeFS()],
	                             'ext3': [filesystem.TuneVolumeFS()],
	                             'ext4': [filesystem.TuneVolumeFS()]}
	tasklist.add(*filesystem_specific_tasks.get(manifest.volume['filesystem'].lower()))


def rollback_tasks(tasklist, tasks_completed, manifest):
	completed = [type(task) for task in tasks_completed]

	def counter_task(task, counter):
		if task in completed and counter not in completed:
			tasklist.add(counter())

	if manifest.volume['backing'].lower() == 'ebs':
		counter_task(ebs.Create, volume.Delete)
		counter_task(volume.Attach, volume.Detach)
	if manifest.volume['backing'].lower() == 's3':
		counter_task(loopback.Create, volume.Delete)
		counter_task(volume.Attach, volume.Detach)
	counter_task(filesystem.CreateMountDir, filesystem.DeleteMountDir)
	counter_task(filesystem.MountVolume, filesystem.UnmountVolume)
	counter_task(filesystem.MountSpecials, filesystem.UnmountSpecials)
