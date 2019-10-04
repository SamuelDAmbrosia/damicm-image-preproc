import argparse
import regex as re
import sys
import os
import inspect

sys.path.append("AutoAnalysis")
import readFits
import PixelDistribution as pd
import PixelStats as ps
import constants as c


class AnalysisOutput(object):
    """Class that contains the information on the output results of the image analysis"""

    def __init__(
        self, filename, nskips=-1, header=[], headerString=""
    ):
        super(AnalysisOutput, self).__init__()

        self.nskips = nskips
        self.entropy = -1
        self.pixelVar= -1
        self.imageVar = -1
        self.imageFitNoise = -1
        self.entropySlope = -1

        self.filename = filename
        self.header = list(header)
        self.headerString = ""

        # Create a header string for writing out to file
        if headerString:
            self.headerString = "filenames\t"
            for s in headerString:
                self.headerString += str(s) + "\t"
            self.headerString += "\n"
        else:
            self.headerString = "filenames\t"
            for s in self.header:
                self.headerString += str(s) + "\t"
            self.headerString += "\n"

    def __str__(self):
        """ Prints information regarding the analysis of an image """
        # Define output string
        outstr = "Analysis of " + self.filename + "\n"

        # Get all the user defined variables that contain information on the image analysis
        classAttributesAndMethods = inspect.getmembers(
            self, lambda a: not (inspect.isroutine(a))
        )
        classAnalysisAttributes = [
            a
            for a in classAttributesAndMethods
            if not (
                a[0].startswith("__")
                and a[0].endswith("__")
                or ("header" in a[0])
                or (a[0] == "filename")
            )
        ]

        # Print the current value of all the analysis variables
        for analysisVar in classAnalysisAttributes:
            outstr += "\t"
            outstr += analysisVar[0] + ": " + str(analysisVar[1])
            outstr += "\n"
        return outstr

    def getTableString(self):
        """ 
            Returns a string of the class values depending on what values we want to return specified in the header attribute 
            For printing values in tabulated format.
        """
        outstr = self.filename + "\t"
        for outVar in self.header:
            outVarValue = self.__getattribute__(outVar)
            try:
                outstr += "%.4g" % outVarValue
            except TypeError:
                outstr += outVarValue
            outstr += "\t"

        outstr += "\n"
        return outstr


def sortAlphaNumeric(x):
    """ Sorts an iterable of strings of alphanumeric data in the expected human way """
    convertToInt = lambda text: int(text) if text.isdigit() else text
    alphanumericKey = lambda key: [convertToInt(c) for c in re.split("([0-9]+)", key)]
    return sorted(x, key=alphanumericKey)


def processImage(filename):
    """
    Function to do enclose the image processing function. Returns an analysisOutput object 
    """

    # Read image
    header, data = readFits.read(filename)

    nskips = header["NDCMS"]
    processHeader = ["nskips", "entropy", "entropySlope", "imageFitNoise", "pixelVar", "imageVar"]
    headerString = ["nskips", "aveImgS", "dS/dskip", "imgNoise", "pixVar", "clustVar"]

    processedImage = AnalysisOutput(filename, nskips=nskips, header=processHeader, headerString=headerString)

    # Compute average image entropy
    processedImage.entropy = pd.imageEntropy(data[:, :, -1])

    # Compute Entropy slope
    entropySlope, entropySlopeErr, _ = pd.imageEntropySlope(data[:, :, :-1])
    processedImage.entropySlope = pd.convertValErrToString((entropySlope, entropySlopeErr))

    # Compute Overall image noise (fit to entire image)
    processedImage.imageFitNoise = pd.computeImageNoise(data[:, :, :-1])

    # Compute pixel noise metrics
    ntrials = 10000
    singlePixelVariance, _ = ps.singlePixelVariance(
        data[:, :, :-1], ntrials=ntrials
    )
    imageNoiseVariance, _ = ps.imageNoiseVariance(
        data[:, :, :-1], nskips - c.SKIPPER_OFFSET, ntrials=ntrials
    )
    processedImage.pixelVar = singlePixelVariance
    processedImage.imageVar = imageNoiseVariance


    return processedImage


def main(argv):
    """
	Command line entry into damic-m image preprocessing code. See printHelp() for use details
		-f - input filenames. Takes a list of strings (command line wildcards) or regex pattern to match. Default is "Img_\\d+.fits"
		-o - output file destination fo the results of the processing. Default is "img_preproc_out.txt"
        -d - directory to search for images and write output to. Default is the current working directory
        -a - flag to reprocess all matched files (even if the results already exist in the output file)
        -r - recursively search through file directotry
	"""

    # Define the parser object
    parser = argparse.ArgumentParser(
        description="Command line interface for damic-m image preprocessing."
    )

    # Add arguments
    parser.add_argument(
        "-f",
        "--filenames",
        nargs="*",
        default=["Img_\\d+.fits"],
        help="Processes all filese that match the string.",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="img_preproc_out.txt",
        help="Output file for preprocessing information.",
    )
    parser.add_argument(
        "-d",
        "--directory",
        default=os.getcwd(),
        help="Directory to search for files.",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="Processes all images that are matched (including ones that have previously been processed).",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively search for images, starting at the provided directory.")

    commandArgs = parser.parse_args()

    # Set command line arguments
    filepath = commandArgs.directory
    outfile = commandArgs.output
    processAll = commandArgs.all
    recursive = commandArgs.recursive


    # Create a list of all subdirectories to search if recursive flag is passed
    searchDirectoryList = []
    for searchDirectory, _, filelist in os.walk(filepath):
        searchDirectoryList.append(searchDirectory)

    if not recursive:
        searchDirectoryList = [searchDirectoryList[0]]

    # Get all files in the directory
    for filepath in searchDirectoryList:
        files = [
            f for f in os.listdir(filepath) if os.path.isfile(os.path.join(filepath, f))
        ]

        files2Process = []

        # Iterate over all the file strings passed to find matches
        for fn in commandArgs.filenames:
            # Define regex matching
            regexPattern = re.compile(fn)
            files2Process.extend(list(filter(regexPattern.match, files)))

        files2Process = sortAlphaNumeric(files2Process)

        # If no files matched, continues
        if len(files2Process) == 0:
            print("No image files matched in " + filepath)
            continue

        # Check what images have already been analyzed and written to file so we do not need to recompute
        outfileFullPath = os.path.join(filepath, outfile)
        try:
            with open(outfileFullPath) as of:
                print("Reading existing processed images")
                existingImgFiles = [line.split()[0] for line in of]
        except FileNotFoundError:
            existingImgFiles = []

        # Process images with functions necessary to characterize the quality of images
        processedImgFiles = []

        print("Processing: ")
        for fp in files2Process:
            print("\t" + os.path.join(filepath, fp), end="")

            # Check to make sure the file has not already been processed
            if not (fp in existingImgFiles) or processAll:

                # Process image
                processedImgFiles.append(processImage(fp))
                print((" ....processed\n", " ....reprocessed\n")[processAll], end="")

            else:
                print(" ....skipped\n", end="")


        # Appends new images to the output file or creates new file if doesn't exist
        if os.path.isfile(outfileFullPath) and not (processAll):
            of = open(outfileFullPath, "a")
        else:
            of = open(outfileFullPath, "w+")
            try:
                of.write(processedImgFiles[0].headerString)
            except IndexError:
                pass

        # Write all the processed data
        for processedImg in processedImgFiles:
            of.write(processedImg.getTableString())
        of.close()

    return


if __name__ == "__main__":
    main(sys.argv[1:])
