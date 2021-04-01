#!/user/bin/env python
# -*- coding:utf-8 -*-
import arcpy
from arcpy import env
import os
from arcpy.sa import ExtractByMask


#Image Composition of the Week
def week_mosaic(inpath,outpath):
    env.workspace = inpath

    f = os.listdir(inpath)
    infiles = ""
    first = f[0]
    end=first
    number=0
    for i in range(len(f)):
        if f[i]==end and f[i].endswith('.tif'):
            #arcpy.SetRasterProperties_management(f[i], "#", "#", "#", "1 -1000")
            infiles += f[i]
            number+=1
            if number==7:
                outfile = first.strip('.tif')+'-'+end
                arcpy.MosaicToNewRaster_management(infiles, outpath, outfile,pixel_type="32_BIT_FLOAT",
                                                   number_of_bands="1",mosaic_method="MEAN")

                infiles=""
                number=0
                if i+1>=len(f):
                    break
                else:
                    first=f[i+1]
            else:
                infiles += ";"
            if end == '089.tif':
                break
            end=f[i+1]

#Extraction of non - residential nighttime light images
def delresident(inpath,outpath):
    env.workspace = inpath
    f = os.listdir(inpath)
    for i in range(len(f)):
        if f[i].endswith('.tif'):
            outfile = outpath + '\\' + f[i]
            outExtractByMask = ExtractByMask(inpath + '\\' + f[i], r"F:\EULUC\city_noresident.tif")
            outExtractByMask.save(outfile)

if __name__=='__main__':
    inpath = r"F:\VNP46\tif\joint"
    outpath = r"F:\VNP46\tif\light_noresident"
    delresident(inpath,outpath)  #Extraction of non - residential nighttime light images

    # Image Composition of the Week
    # (This is the method for generating weekly composite data in bulk.
    # If a image of an area needs to be manually removed, the composite is done directly using arcgis)
    weekpath=r"F:\VNP46\tif\week"
    week_mosaic(outpath,weekpath)


