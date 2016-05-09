import numpy

latency_and_loss = ["UA-627-20150224 MSS loss: 0.0601092896175 latency: 761.047304948",
					"UA-3504-20150222 DA2GC loss: 0.0333333333333 latency: 262.016034843",
					"US-534-20150304 DA2GC loss: 0.0115789473684 latency: 246.22346177",
					"UA-401-20150308 MSS loss: 0.0623287671233 latency: 770.68298452",
					"DL-2374-20150313 DA2GC loss: 0.0195555555556 latency: 312.729272197",
					"SW-2374-20150310 MSS loss: 0.0616666666667 latency: 822.5737164",
					"UA-240-20150316 MSS loss: 0.0461764705882 latency: 726.001333231",
					"AA-153-20151026 DA2GC loss: 0.311836734694 latency: 1011.17364294",
					#"SW-2043-20151129 MSS loss: 1.0 latency: nan",
					"UA-946-20150705 MSS loss: 0.101923076923 latency: 854.870763307",
					"LH-475 MSS loss: 0.0594545454545 latency: 863.790398208",
					"UA-1251-20150929 MSS loss: 0.0471794871795 latency: 739.409074252",
					"UA-1279-20150930 MSS loss: 0.05625 latency: 719.636102428",
					"UA-398-20150705 MSS loss: 0.0655172413793 latency: 749.318827798",
					"UA-531-20150929 MSS loss: 0.18462962963 latency: 1153.20570259",
					"UA-946-20150705 MSS loss: 0.101923076923 latency: 854.870763307",
					"UA-986-20150913 MSS loss: 0.104135802469 latency: 657.178959912"]

throughput = ["UA-627-20150224 MSS up: 218.154761905 down: 2389.86426077",
				"UA-3504-20150222 DA2GC up: 161.509090909 down: 468.072777309",
				"US-534-20150304 DA2GC up: 165.881355932 down: 344.516774855",
				"UA-401-20150308 MSS up: 259.545454545 down: 1984.83915051",
				"DL-2374-20150313 DA2GC up: 161.488636364 down: 458.63109359",
				"SW-2374-20150310 MSS up: 547.396825397 down: 71.479896853",
				"UA-240-20150316 MSS up: 253.666666667 down: 2554.09841312",
				"AA-153-20151026 DA2GC up: 133.791044776 down: 1334.13901961",
				"SW-2043-20151129 MSS up: 153.909090909 down: 2471.40385567",
				"UA-946-20150705 MSS up: 62.6285714286 down: 1563.67040827",
				"LH-475 MSS up: 119.914285714 down: 1048.69931456",
				"UA-1251-20150929 MSS up: 182.789473684 down: 13878.9912795",
				"UA-398-20150705 MSS up: 3068.1122449 down: 8823.23724037",
				"UA-531-20150929 MSS up: 78.696969697 down: 1507.48929259",
				"UA-946-20150705 MSS up: 62.6285714286 down: 1563.67040827",
				"UA-986-20150913 MSS up: 136.857142857 down: 1936.57322822"]

latencies = []
for stat in latency_and_loss:
	latencies.append(float(stat.split(' ')[-1]))

down_throughputs = []
up_throughputs = []
for stat in throughput:
	down_throughputs.append(float(stat.split(' ')[-1]))
	up_throughputs.append(float(stat.split(' ')[-3]))

print("avg latency: "+"{0:.1f}".format(numpy.average(latencies))+" ms")
print("avg up throughput: "+"{0:.1f}".format(numpy.average(up_throughputs))+" Kbps")
print("avg down throughput: "+"{0:.1f}".format(numpy.average(down_throughputs))+" Kbps")
print("")
print("median latency: "+"{0:.1f}".format(numpy.median(latencies))+" ms")
print("median up throughput: "+"{0:.1f}".format(numpy.median(up_throughputs))+" Kbps")
print("median down throughput: "+"{0:.1f}".format(numpy.median(down_throughputs))+" Kbps")


