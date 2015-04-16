import urllib2
import zipfile
import os
from StringIO import StringIO

REP_LINK = "https://github.com/falceeffect/MayaCUI/archive/master.zip" # link to GitHub repo with MayaCUI source code
EXCLUDE_LIST = [".gitignore", "cui.todo", "README.md"] # repository files, which are not interesting for the end-user

zipData = StringIO(urllib2.urlopen(REP_LINK).read()) # load repo ZIP archive

zipFile = zipfile.ZipFile(zipData) # load ZIP contents into memory
for filePath in zipFile.namelist():
  filename = filePath.split('/')[-1] 
  if not filename or filename in EXCLUDE_LIST:
    continue # truncate excluded files and directories

  src = zipFile.open(filePath) # open source file from the archive
  dest = open(filename, "wb") # open end file
  dest.write(src.read()) # copy binary data
  src.close()
  dest.close()
zipFile.close()

scriptDir = os.path.dirname(os.path.realpath(__file__)) # get the location of this script 

for filename in os.listdir(scriptDir):
  if filename.endswith(".pyc"):
    os.remove(filename) # remove all old python byte-code files