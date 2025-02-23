import os
import glob
import argparse
from tqdm import tqdm
from omegaconf import OmegaConf

from genie.sampler.scaffold import ScaffoldSampler
from genie.utils.multiprocessor import MultiProcessor
from genie.utils.model_io import load_pretrained_model


class ScaffoldRunner(MultiProcessor):
	"""
	A multi-processing runner for sampling scaffold given motif specifications.
	"""

	def create_tasks(self, args):
		"""
		Define a set of tasks to be distributed across processes.

		Args:
			params:
				A dictionary of parameters.

		Returns:
			tasks:
				A list of tasks to be distributed across processes, where 
				each task is represented as a dictionary of task-specific 
				parameters.
		"""

		# Initialize
		tasks = []

		# Define motif names
		if args["motif_name"] is not None:
			motif_names = args["motif_name"]
		else:
			motif_names = [
				filepath.split('/')[-1].split('.')[0]
				for filepath in glob.glob(os.path.join(args["datadir"], '*.pdb'))
			]

		# Create tasks
		for motif_name in motif_names:
			tasks.append({
				'motif_name': motif_name
			})

		return tasks

	def create_constants(self, params):
		"""
		Define a dictionary of constants shared across processes.

		Args:
			params:
				A dictionary of parameters.

		Returns:
			constants:
				A dictionary of constants shared across processes.
		"""

		# Define
		names = [
			'rootdir', 'name', 'epoch', 'scale', 'strength',
			'outdir', 'num_samples', 'batch_size', 'datadir', 'structures'
		]

		# Create constants
		constants = dict([(name, params[name]) for name in names])

		return constants

	def execute(self, constants, tasks, device):
		"""
		Execute a set of assigned tasks on a given device.

		Args:
			constants:
				A dictionary of constants.
			tasks:
				A list of tasks, where each task is represented as a 
				dictionary of task-specific parameters.
			device:
				Name of device to execute on.
		"""

		# Load model
		model = load_pretrained_model(
			constants['rootdir'],
			constants['name'],
			constants['epoch']
		).eval().to(device)

		# Load sampler
		sampler = ScaffoldSampler(model)

		# Iterate through all tasks
		for task in tqdm(tasks, desc=device):

			# Define output directory
			outdir = constants['outdir']

			# Initialize
			num_samples = constants['num_samples']

			# Sample
			while num_samples > 0:

				# Define
				batch_size = min(constants['batch_size'], num_samples)
				filepath = os.path.join(
					constants['datadir'],
					'{}.pdb'.format(task['motif_name'])
				)

				# Initialize parameters
				params = {
					'filepath': filepath,
					'scale': constants['scale'],
					'strength': constants['strength'],
					'num_samples': batch_size,
					'outdir': outdir,
					'prefix': task['motif_name'],
					'offset': constants['num_samples'] - num_samples,
					'structures': constants['structures']
				}

				# Sample
				sampler.sample(params)

				# Update
				num_samples -= batch_size


def main(args):

	# Define multiprocessor runner
	runner = ScaffoldRunner()

	# Run
	runner.run(vars(args), args.num_devices)

def run_scaffold(config_file):

	conf = OmegaConf.load(config_file)

	# Create parser
	parser = argparse.ArgumentParser()

	# Define model arguments
	parser.add_argument('--name', type=str, help='Model name', default=conf.genie2.name)
	parser.add_argument('--epoch', type=int, help='Model epoch', default=conf.genie2.epoch)
	parser.add_argument('--rootdir', type=str, help='Root directory', default=conf.genie2.rootdir)

	# Define sampling arguments
	parser.add_argument('--scale', type=float, help='Sampling noise scale', default=conf.genie2.scale)
	parser.add_argument('--outdir', type=str, help='Output directory', default=conf.genie2.outdir)
	parser.add_argument('--strength', type=float, help='Sampling classifier-free strength', default=conf.genie2.strength)
	parser.add_argument('--num_samples', type=int, help='Number of samples per length', default=conf.genie2.num_samples)
	parser.add_argument('--batch_size', type=int, help='Batch size', default=conf.genie2.batch_size)
	parser.add_argument('--motif_name', type=str, help='Motif name', default=conf.genie2.motif_name)
	parser.add_argument('--datadir', type=str, help='Data directory', default=conf.genie2.datadir)
	
	# Define environment arguments
	parser.add_argument('--num_devices', type=int, help='Number of GPU devices', default=conf.genie2.num_devices)

	# Define structures for motif scaffolding
	parser.add_argument('--structures', type=str, help='Contig map', default="".join(conf.genie2.contigs))

	args, unknown = parser.parse_known_args()

	# Run
	main(args)


if __name__ == '__main__':

	# Create parser
	parser = argparse.ArgumentParser()

	# Define model arguments
	parser.add_argument('--name', type=str, help='Model name', required=True)
	parser.add_argument('--epoch', type=int, help='Model epoch', required=True)
	parser.add_argument('--rootdir', type=str, help='Root directory', default='results')

	# Define sampling arguments
	parser.add_argument('--scale', type=float, help='Sampling noise scale', required=True)
	parser.add_argument('--outdir', type=str, help='Output directory', required=True)
	parser.add_argument('--strength', type=float, help='Sampling classifier-free strength', default=0)
	parser.add_argument('--num_samples', type=int, help='Number of samples per length', default=100)
	parser.add_argument('--batch_size', type=int, help='Batch size', default=4)
	parser.add_argument('--motif_name', type=str, help='Motif name', default=None)
	parser.add_argument('--datadir', type=str, help='Data directory', default='data/design25')
	
	# Define environment arguments
	parser.add_argument('--num_devices', type=int, help='Number of GPU devices', default=1)
	parser.add_argument('--structures', type=str, help='Contig map for motif specification', default=None)

	# Parse arguments
	args = parser.parse_args()

	# Run
	main(args)
