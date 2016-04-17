import csv

class my_csv:
	"""
	A python dictionary where the keys are the first column in a .csv file.
	Each value is a dictionary that represents the rest of the row of the 
	.csv file which corresponds to that key.
	"""

	# constructor
	def __init__(self, input_obj):
		if type(input_obj) == type(""):
			self.dict = {}
			self.headings = []
			self.buildDictFromCSV(input_obj)
		elif type(input_obj) == type({}):
			self.dict = input_obj
			self.headings = ['key']
			self.getHeadingsFromDict()

	def buildDictFromCSV(self, filename):

		with open(filename, 'r') as csvfile:
			reader = csv.reader(csvfile)
			i = 0
			for row in reader:
				pkey = row[0]
				if i == 0:
					self.headings = row
				else:
					self.dict[pkey] = {}
					j = 0
					for this_subkey in self.headings:
						if j != 0:
							self.dict[pkey][this_subkey] = row[j]
						j+=1
				i += 1

	def getHeadingsFromDict(self):
		first_dict = self.dict[self.dict.keys()[0]]
		for this_subkey in first_dict:
			self.headings.append(this_subkey)
		return

	def writeToCSV(self, output_fname):
		with open(output_fname, 'w') as csvfile:
			writer = csv.writer(csvfile)
			writer.writerow(self.headings)
			for pkey in self.dict:
				this_row = self.dictToRow(pkey)
				writer.writerow(this_row)

	def dictToRow(self, pkey):
		row = [pkey]
		for key in self.dict[pkey]:
			row.append(self.dict[pkey][key])

		return row

