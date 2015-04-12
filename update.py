import urllib2
import zipfile
import os
from StringIO import StringIO

REP_LINK = "https://github.com/falceeffect/MayaCUI/archive/master.zip"
EXCLUDE_LIST = [".gitignore", "cui.todo", "README.md"]

zipData = StringIO(urllib2.urlopen(REP_LINK).read())

zipFile = zipfile.ZipFile(zipData)
for filePath in zipFile.namelist():
  filename = filePath.split('/')[-1]
  if not filename or filename in EXCLUDE_LIST:
    continue

  src = zipFile.open(filePath)
  dest = open(filename, "wb")
  dest.write(src.read())
  src.close()
  dest.close()
zipFile.close()

scriptDir = os.path.dirname(os.path.realpath(__file__)) 

for filename in os.listdir(scriptDir):
  if filename.endswith(".pyc"):
    os.remove(filename)