import matplotlib.pyplot as plt
import sys
import csv
import numpy as np

def graphStoO(setting, output, imgcsv):
    '''
    Generates a graph showing relationship between one setting var and one output var
    '''
    
    sets = []
    outs = []
    
    with open(imgcsv, newline='') as csvfile:
        imgreader = csv.DictReader(csvfile, delimiter = ',', quotechar='|')
        for img in imgreader:
            
            #for key in img
            
            sets.append(float(img[str(setting)]))
            outs.append(float(img[str(output)]))
    

    x = np.array(sets)
    y = np.array(outs)
    
    colors = 'blue'
    area = 7

    plt.scatter(x, y, s=area, c=colors, alpha=0.5)
    plt.title(setting + " to " + output)
    plt.xlabel(setting)
    plt.ylabel(output)
    plt.show()
    
def main(params):
    
    imgcsv = sys.argv[1]
    setting = sys.argv[2]
    output = sys.argv[3]
    
    graphStoO(setting, output, imgcsv)

main(sys.argv)