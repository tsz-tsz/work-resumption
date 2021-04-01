#!/user/bin/env python
# -*- coding:utf-8 -*-
import os
import rw_tif
import numpy as np
from osgeo import gdal



#VNP46A1 data conversion from hdf format to tif format
#layer1:DNB at sensor radiance layer; layer2:lunar zenith layer; layer 3:QF cloud mask lyaer; layer 4:UTC time layer
def VNP_tif(inpath,outpath,layer1,layer2,layer3,layer4):
    if not os.path.exists(os.path.join(outpath,'light')):
        os.makedirs(os.path.join(outpath,'light'))
    if not os.path.exists(os.path.join(outpath,'cloud')):
        os.makedirs(os.path.join(outpath,'cloud'))
    if not os.path.exists(os.path.join(outpath,'angle')):
        os.makedirs(os.path.join(outpath,'angle'))
    if not os.path.exists(os.path.join(outpath,'time')):
        os.makedirs(os.path.join(outpath,'time'))

    f = os.listdir(inpath)
    for i in range(len(f)):
        if f[i].endswith('.h5'):
            infile = inpath + '//' + f[i]
            root_ds = gdal.Open(infile)
            ds_list = root_ds.GetSubDatasets()
            rlayer = gdal.Open(ds_list[layer1][0], gdal.GA_ReadOnly)
            alayer=gdal.Open(ds_list[layer2][0], gdal.GA_ReadOnly)
            clayer = gdal.Open(ds_list[layer3][0], gdal.GA_ReadOnly)
            tlayer=gdal.Open(ds_list[layer4][0], gdal.GA_ReadOnly)

            # collect bounding box coordinates
            # -a_ullr <ulx> <uly> <lrx> <lry>
            #a = rlayer.GetMetadata_Dict()
            WestBoundCoord = rlayer.GetMetadata_Dict()["HDFEOS_GRIDS_VNP_Grid_DNB_WestBoundingCoord"]
            EastBoundCoord = rlayer.GetMetadata_Dict()["HDFEOS_GRIDS_VNP_Grid_DNB_EastBoundingCoord"]
            NorthBoundCoord = rlayer.GetMetadata_Dict()["HDFEOS_GRIDS_VNP_Grid_DNB_NorthBoundingCoord"]
            SouthBoundCoord = rlayer.GetMetadata_Dict()["HDFEOS_GRIDS_VNP_Grid_DNB_SouthBoundingCoord"]
            EPSG = "-a_srs EPSG:4326"  # WGS84

            translateOptionText = EPSG + " -a_ullr " + WestBoundCoord + " " + NorthBoundCoord + " " + EastBoundCoord + " " + SouthBoundCoord

            translateoptions = gdal.TranslateOptions(gdal.ParseCommandLine(translateOptionText))

            outfile = outpath + '\\light\\' + f[i].strip('.h5') + '.tif'
            gdal.Translate(outfile, clayer, options=translateoptions)

            im_datas = alayer.GetRasterBand(1).ReadAsArray()
            min=np.min(im_datas[im_datas>0])
            if min<9000 :
                outfilea=outpath+ '\\angle\\' + f[i].strip('.h5') + '.tif'
                gdal.Translate(outfilea, alayer, options=translateoptions)

                outfilet = outpath + '\\time\\' + f[i].strip('.h5') + '.tif'
                gdal.Translate(outfilet, tlayer, options=translateoptions)

#MOD09A1 band 1, 2, and 4 averaged , then merge
def MOD_tif(inpath,outpath,layer1,layer2,layer3):
    f = os.listdir(inpath)
    day = f[0][13:16]
    indata = []
    for i in range(len(f)):
        if f[i].endswith('.hdf') and f[i][13:16] ==day:
            infile = inpath + '\\' + f[i]
            root_ds = gdal.Open(infile)
            ds_list = root_ds.GetSubDatasets()
            data1,im_proj, im_geotrans,_,_,_=rw_tif.read(ds_list[layer1][0])
            data2,_,_,_,_,_=rw_tif.read(ds_list[layer2][0])
            data3,_,_,_,_,_=rw_tif.read(ds_list[layer3][0])
            dev=np.ones(data1.shape)    #Number of valid values of each pixel
            r=np.where((data1>-101 )&(data2 >-101))
            data1[r]+=data2[r]
            dev[r]+=1
            r=np.where((data1<-100 )&(data2>-101 ))
            data1[r]=data2[r]
            r = np.where((data1>-101 )&(data3 >-101))
            data1[r] += data3[r]
            dev[r] += 1
            r = np.where((data1<-100 )&(data3>-101 ))
            data1[r] = data3[r]
            data1=data1/dev
            outfile = outpath + '\\' + f[i].strip('.hdf') + '.tif'
            rw_tif.write(outfile, im_proj, im_geotrans,data1)
            del data1,data2,data3,dev
            indata.append(outfile)
            if i==len(f)-1:
                outfile_m = outpath + '\\' + f[i-1][:16] + '.tif'
                gdal.Warp(outfile_m, indata)
                for j in indata:
                    os.remove(j)
            elif f[i+1][13:16]!=day:
                outfile_m=outpath+'\\'+f[i][:13]+day+'.tif'
                gdal.Warp(outfile_m, indata)
                day=f[i+1][13:16]
                for j in indata:
                    os.remove(j)
                indata=[]


#Cropping and resampling of surface reflectance data based on NTL imagery
def reflect_resample(inpath,outpath,anglepath):
    fa = os.listdir(anglepath)
    fr = os.listdir(inpath)
    for i in fa:
        for j in fr:
            if len(j) == 20:
                reflect_day = int(j[13:16])
                if int(i[13:16]) >= reflect_day and int(i[13:16]) <= reflect_day+7:
                    reflect_tm = inpath + '//' + j
                    reflect_t = outpath + '//' + i
                    angle_t = anglepath + '//' + i
                    adata, im_proj, im_geotrans, im_width, im_height,_ = rw_tif.read(angle_t)
                    minX = im_geotrans[0]
                    maxY = im_geotrans[3]
                    maxX = im_geotrans[0] + im_width * im_geotrans[1] + im_height * im_geotrans[2]
                    minY = im_geotrans[3] + im_width * im_geotrans[4] + im_height * im_geotrans[5]
                    gdal.Warp(reflect_t, reflect_tm, outputBounds=(minX, minY, maxX, maxY), dstSRS=im_proj,
                              xRes=im_geotrans[1],yRes=abs(im_geotrans[5]), resampleAlg=gdal.GRIORA_Bilinear, dstNodata=0)
                    break


if __name__=='__main__':
    os.chdir('F:\\VNP46')     #Folder path for VNP46A1 nighttime lights data
    VNP_tif('raw','tif',4,8,11,25)  #VNP46A1 data conversion from hdf format to tif format

    reflect_rp = r'F:\MOD09\raw'  # path for MOD09A1 raw data
    reflect_tmp = r'F:\MOD09\tif'  # path for MOD09A1 tif format data
    MOD_tif(reflect_rp, reflect_tmp, 0, 1, 3)   #MOD09A1 band 1, 2, and 4 averaged , then merge
    angle_tp = 'tif\\angle'  # path for VNP46A1 lunar zenith image
    reflect_tp = 'tif\\reflect'  # path for surface reflectance data data after processing according to NTL data
    reflect_resample(reflect_tmp, reflect_tp, angle_tp)  #Cropping and resampling of surface reflectance data based on NTL imagery
